from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db
from app.expert_system.engine import RuleEngine
from app.models import get_all_disasters, get_disaster_by_id, get_affected_areas_by_disaster, get_unacknowledged_alerts, get_recent_activity_logs, log_activity, create_alert
from app.routes.auth_routes import login_required
from datetime import datetime
import json

disaster_bp = Blueprint("disaster", __name__)

@disaster_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("index.html")

@disaster_bp.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    disasters = conn.execute("SELECT * FROM disasters ORDER BY id DESC").fetchall()
    messages = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 15").fetchall()

    # Metrics calculation
    active_count = len([d for d in disasters if d["status"] == "ACTIVE"])
    critical_areas_count = conn.execute("SELECT COUNT(*) FROM affected_areas WHERE calculated_priority = 'CRITICAL'").fetchone()[0]
    high_areas_count = conn.execute("SELECT COUNT(*) FROM affected_areas WHERE calculated_priority = 'HIGH'").fetchone()[0]

    avail_amb = conn.execute("SELECT SUM(quantity) FROM resources WHERE resource_type = 'Ambulances' AND status = 'Available'").fetchone()[0] or 0
    avail_teams = conn.execute("SELECT SUM(quantity) FROM resources WHERE resource_type = 'Rescue teams' AND status = 'Available'").fetchone()[0] or 0
    avail_beds = conn.execute("SELECT SUM(quantity) FROM resources WHERE resource_type = 'Hospital beds' AND status = 'Available'").fetchone()[0] or 0
    avail_shelters = conn.execute("SELECT SUM(quantity) FROM resources WHERE resource_type = 'Shelters' AND status = 'Available'").fetchone()[0] or 0

    pending_decisions = conn.execute("SELECT COUNT(*) FROM gdss_decisions WHERE status = 'OPEN'").fetchone()[0]

    alerts = get_unacknowledged_alerts()
    activities = get_recent_activity_logs(15)

    conn.close()

    return render_template(
        "dashboard.html",
        disasters=disasters,
        messages=messages,
        active_count=active_count,
        critical_areas_count=critical_areas_count,
        high_areas_count=high_areas_count,
        avail_amb=avail_amb,
        avail_teams=avail_teams,
        avail_beds=avail_beds,
        avail_shelters=avail_shelters,
        pending_decisions=pending_decisions,
        alerts=alerts,
        activities=activities
    )

@disaster_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    disaster_type = request.form.get("disaster_type")
    location = request.form.get("location")
    people_affected = int(request.form.get("people_affected", 0))
    medical_emergency = request.form.get("medical_emergency")
    road_status = request.form.get("road_status")
    ambulances = int(request.form.get("ambulances", 0))
    hospital_beds = int(request.form.get("hospital_beds", 0))

    # Optional multi-area inputs from form
    area_names = request.form.getlist("area_name[]")
    area_populations = request.form.getlist("area_population[]")
    area_medicals = request.form.getlist("area_medical[]")
    area_roads = request.form.getlist("area_road[]")

    # Specific disaster metric fields
    specific_metrics = {}
    if disaster_type == "Flood":
        specific_metrics["water_level"] = float(request.form.get("water_level", 0.0))
        specific_metrics["rainfall"] = float(request.form.get("rainfall", 0.0))
        specific_metrics["evacuation_needed"] = bool(request.form.get("evacuation_needed"))
    elif disaster_type == "Earthquake":
        specific_metrics["building_damage_pct"] = float(request.form.get("building_damage_pct", 0.0))
        specific_metrics["trapped_people"] = int(request.form.get("trapped_people", 0))
    elif disaster_type == "Cyclone":
        specific_metrics["wind_speed_kmh"] = float(request.form.get("wind_speed_kmh", 0.0))
        specific_metrics["coastal_surge_risk"] = request.form.get("coastal_surge_risk", "LOW")
    elif disaster_type == "Fire":
        specific_metrics["fire_severity"] = request.form.get("fire_severity", "LOW")
        specific_metrics["smoke_hazard"] = request.form.get("smoke_hazard", "LOW")
    elif disaster_type == "Landslide":
        specific_metrics["terrain_risk"] = request.form.get("terrain_risk", "LOW")

    engine = RuleEngine()

    # Primary disaster analysis
    primary_input = {
        "people_affected": people_affected,
        "medical_emergency": medical_emergency,
        "road_status": road_status,
        "ambulances": ambulances,
        "hospital_beds": hospital_beds,
        "specific_metrics": specific_metrics
    }
    result = engine.evaluate_area(disaster_type, primary_input)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO disasters
        (disaster_type, location, people_affected, medical_emergency, road_status,
         available_ambulances, hospital_beds, priority, recommendation, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
    """, (
        disaster_type, location, people_affected, medical_emergency, road_status,
        ambulances, hospital_beds, result["priority"], result["text_recommendation"], now_str
    ))
    disaster_id = cursor.lastrowid

    # Evaluate & Store Multi-Areas if provided
    evaluated_areas = []
    if area_names:
        for idx, aname in enumerate(area_names):
            if not aname.strip():
                continue
            apop = int(area_populations[idx]) if idx < len(area_populations) and area_populations[idx] else 100
            amed = area_medicals[idx] if idx < len(area_medicals) else "LOW"
            aroad = area_roads[idx] if idx < len(area_roads) else "ACCESSIBLE"

            area_eval = engine.evaluate_area(disaster_type, {
                "area_name": aname,
                "people_affected": apop,
                "medical_emergency": amed,
                "road_status": aroad,
                "ambulances": ambulances,
                "hospital_beds": hospital_beds,
                "specific_metrics": specific_metrics
            })

            cursor.execute("""
                INSERT INTO affected_areas
                (disaster_id, area_name, people_affected, medical_emergency, road_status,
                 specific_metrics_json, calculated_priority, reasoning_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                disaster_id, aname, apop, amed, aroad,
                json.dumps(specific_metrics), area_eval["priority"],
                json.dumps(area_eval["reasons"]), now_str
            ))
            evaluated_areas.append({
                "area_name": aname,
                "people_affected": apop,
                "priority": area_eval["priority"],
                "reasons": area_eval["reasons"]
            })
    else:
        # Save default primary area
        cursor.execute("""
            INSERT INTO affected_areas
            (disaster_id, area_name, people_affected, medical_emergency, road_status,
             specific_metrics_json, calculated_priority, reasoning_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            disaster_id, location, people_affected, medical_emergency, road_status,
            json.dumps(specific_metrics), result["priority"],
            json.dumps(result["reasons"]), now_str
        ))

    # Auto-generate Allocation Recommendations in resource_allocations table
    for rtype, req_qty in result["resource_recommendations"].items():
        if req_qty > 0:
            cursor.execute("""
                INSERT INTO resource_allocations
                (disaster_id, resource_type, recommended_qty, status, requested_by, updated_at)
                VALUES (?, ?, ?, 'PENDING', ?, ?)
            """, (disaster_id, rtype, req_qty, session.get("username", "System"), now_str))

    conn.commit()
    conn.close()

    # Create Alert if Critical
    if result["priority"] == "CRITICAL":
        create_alert("CRITICAL", f"CRITICAL DISASTER ALERT: {disaster_type} at {location}",
                     f"Immediate response required for {people_affected} affected individuals.")

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "ANALYZE_DISASTER", f"Analyzed {disaster_type} disaster at {location} -> Priority: {result['priority']}")


    return render_template(
        "result.html",
        disaster_id=disaster_id,
        disaster_type=disaster_type,
        location=location,
        people_affected=people_affected,
        medical_emergency=medical_emergency,
        road_status=road_status,
        priority=result["priority"],
        score=result["score"],
        recommendation=result["text_recommendation"],
        resource_recommendations=result["resource_recommendations"],
        reasons=result["reasons"],
        triggered_rules=result["triggered_rules"],
        evaluated_areas=evaluated_areas
    )

@disaster_bp.route("/disaster/<int:disaster_id>/explain")
@login_required
def explain(disaster_id):
    disaster = get_disaster_by_id(disaster_id)
    if not disaster:
        flash("Disaster incident not found.", "warning")
        return redirect(url_for("disaster.dashboard"))

    areas = get_affected_areas_by_disaster(disaster_id)

    engine = RuleEngine()
    eval_result = engine.evaluate_area(disaster["disaster_type"], {
        "people_affected": disaster["people_affected"],
        "medical_emergency": disaster["medical_emergency"],
        "road_status": disaster["road_status"],
        "ambulances": disaster["available_ambulances"],
        "hospital_beds": disaster["hospital_beds"]
    })

    return render_template(
        "result.html",
        disaster_id=disaster["id"],
        disaster_type=disaster["disaster_type"],
        location=disaster["location"],
        people_affected=disaster["people_affected"],
        medical_emergency=disaster["medical_emergency"],
        road_status=disaster["road_status"],
        priority=disaster["priority"],
        score=eval_result["score"],
        recommendation=disaster["recommendation"],
        resource_recommendations=eval_result["resource_recommendations"],
        reasons=eval_result["reasons"],
        triggered_rules=eval_result["triggered_rules"],
        evaluated_areas=areas
    )
