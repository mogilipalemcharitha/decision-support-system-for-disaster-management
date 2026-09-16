from flask import Blueprint, render_template, jsonify, session
from app.db import get_db
from app.routes.auth_routes import login_required

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def index():
    conn = get_db()

    # Disaster Counts by Priority
    priorities = conn.execute("""
        SELECT calculated_priority, COUNT(*) as count
        FROM affected_areas
        GROUP BY calculated_priority
    """).fetchall()
    priority_dict = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for p in priorities:
        if p["calculated_priority"] in priority_dict:
            priority_dict[p["calculated_priority"]] = p["count"]

    # Disaster Counts by Type
    types = conn.execute("""
        SELECT disaster_type, COUNT(*) as count
        FROM disasters
        GROUP BY disaster_type
    """).fetchall()
    type_dict = {t["disaster_type"]: t["count"] for t in types}

    # Resource Utilization Metrics
    resources = conn.execute("SELECT resource_type, SUM(quantity) as total FROM resources GROUP BY resource_type").fetchall()
    resource_dict = {r["resource_type"]: r["total"] for r in resources}

    # Evaluation Metrics
    total_disasters = conn.execute("SELECT COUNT(*) FROM disasters").fetchone()[0]
    total_affected_pop = conn.execute("SELECT SUM(people_affected) FROM disasters").fetchone()[0] or 0
    total_decisions_made = conn.execute("SELECT COUNT(*) FROM gdss_decisions WHERE status = 'FINALIZED'").fetchone()[0]
    total_votes_cast = conn.execute("SELECT COUNT(*) FROM gdss_votes").fetchone()[0]
    total_alerts_gen = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    total_activities = conn.execute("SELECT COUNT(*) FROM activity_logs").fetchone()[0]

    # Calculate average consensus percentage across finalized decisions
    decisions = conn.execute("SELECT id FROM gdss_decisions WHERE status = 'FINALIZED'").fetchall()
    avg_consensus = 0.0
    if decisions:
        total_consensus = 0.0
        for d in decisions:
            votes = conn.execute("SELECT vote_option FROM gdss_votes WHERE decision_id = ?", (d["id"],)).fetchall()
            if votes:
                counts = {}
                for v in votes:
                    counts[v["vote_option"]] = counts.get(v["vote_option"], 0) + 1
                max_v = max(counts.values())
                total_consensus += (max_v / len(votes)) * 100
        avg_consensus = round(total_consensus / len(decisions), 1)

    conn.close()

    return render_template(
        "analytics.html",
        priority_dict=priority_dict,
        type_dict=type_dict,
        resource_dict=resource_dict,
        total_disasters=total_disasters,
        total_affected_pop=total_affected_pop,
        total_decisions_made=total_decisions_made,
        total_votes_cast=total_votes_cast,
        total_alerts_gen=total_alerts_gen,
        total_activities=total_activities,
        avg_consensus=avg_consensus
    )

@analytics_bp.route("/api/map_data")
@login_required
def map_data():
    """
    Returns spatial coordinate data for Leaflet Map visualization.
    Uses sample geocoded coordinates mapped to locations.
    """
    conn = get_db()
    disasters = conn.execute("SELECT * FROM disasters ORDER BY id DESC").fetchall()
    resources = conn.execute("SELECT * FROM resources").fetchall()
    conn.close()

    # Pre-defined mock coordinates for sample demonstration locations
    location_coords = {
        "Downtown": {"lat": 17.3850, "lng": 78.4867},
        "North Suburb": {"lat": 17.4399, "lng": 78.4983},
        "East Coast Bay": {"lat": 17.3616, "lng": 78.4747},
        "Central Station": {"lat": 17.3984, "lng": 78.4722},
        "City Hospital": {"lat": 17.4126, "lng": 78.4497},
        "Relief Warehouse": {"lat": 17.4000, "lng": 78.4600}
    }

    map_markers = []
    for d in disasters:
        loc = d["location"]
        coords = location_coords.get(loc, {"lat": 17.3850 + (d["id"] * 0.01), "lng": 78.4867 + (d["id"] * 0.01)})
        map_markers.append({
            "type": "disaster",
            "title": f"{d['disaster_type']} - {loc}",
            "priority": d["priority"],
            "lat": coords["lat"],
            "lng": coords["lng"],
            "details": f"Affected: {d['people_affected']} | Priority: {d['priority']}"
        })

    for r in resources:
        loc = r["location"]
        coords = location_coords.get(loc, {"lat": 17.4100 + (r["id"] * 0.005), "lng": 78.4500 + (r["id"] * 0.005)})
        map_markers.append({
            "type": "resource",
            "title": f"Resource: {r['name']} ({r['resource_type']})",
            "status": r["status"],
            "lat": coords["lat"],
            "lng": coords["lng"],
            "details": f"Qty: {r['quantity']} | Status: {r['status']}"
        })

    return jsonify({"markers": map_markers})
