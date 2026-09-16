from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db
from app.models import get_all_resources, log_activity, create_alert
from app.routes.auth_routes import login_required, roles_required
from datetime import datetime

resource_bp = Blueprint("resource", __name__)

@resource_bp.route("/resources")
@login_required
def index():
    resources = get_all_resources()
    conn = get_db()
    allocations = conn.execute("""
        SELECT ra.*, d.disaster_type, d.location
        FROM resource_allocations ra
        JOIN disasters d ON ra.disaster_id = d.id
        ORDER BY ra.id DESC
    """).fetchall()
    conn.close()
    return render_template("resources.html", resources=resources, allocations=allocations)

@resource_bp.route("/resources/add", methods=["POST"])
@login_required
@roles_required("System Administrator", "Disaster Management Authority", "Police", "Fire & Rescue", "Medical/Ambulance Team", "Hospital", "NGO/Volunteer")
def add_resource():
    name = request.form.get("name")
    resource_type = request.form.get("resource_type")
    quantity = int(request.form.get("quantity", 1))
    location = request.form.get("location")
    status = request.form.get("status", "Available")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        INSERT INTO resources (name, resource_type, quantity, location, status, last_updated_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, resource_type, quantity, location, status, now_str))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "ADD_RESOURCE", f"Added {quantity} x {name} ({resource_type}) at {location}")
    flash(f"Resource '{name}' registered successfully!", "success")
    return redirect(url_for("resource.index"))

@resource_bp.route("/resources/update/<int:resource_id>", methods=["POST"])
@login_required
def update_resource(resource_id):
    quantity = int(request.form.get("quantity"))
    status = request.form.get("status")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        UPDATE resources
        SET quantity = ?, status = ?, last_updated_time = ?
        WHERE id = ?
    """, (quantity, status, now_str, resource_id))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "UPDATE_RESOURCE", f"Updated resource #{resource_id} status to {status}, Qty: {quantity}")
    flash("Resource status updated.", "info")
    return redirect(url_for("resource.index"))

@resource_bp.route("/resources/allocation/<int:allocation_id>/action", methods=["POST"])
@login_required
@roles_required("System Administrator", "Disaster Management Authority")
def allocation_action(allocation_id):
    action = request.form.get("action") # 'APPROVE' or 'REJECT'
    approved_qty = int(request.form.get("approved_qty", 0))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()

    if action == "APPROVE":
        conn.execute("""
            UPDATE resource_allocations
            SET status = 'APPROVED', approved_qty = ?, approved_by = ?, updated_at = ?
            WHERE id = ?
        """, (approved_qty, session.get("username"), now_str, allocation_id))
        log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                     "APPROVE_ALLOCATION", f"Approved allocation proposal #{allocation_id} for {approved_qty} units")
        flash(f"Allocation proposal #{allocation_id} APPROVED!", "success")
    else:
        conn.execute("""
            UPDATE resource_allocations
            SET status = 'REJECTED', approved_by = ?, updated_at = ?
            WHERE id = ?
        """, (session.get("username"), now_str, allocation_id))
        log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                     "REJECT_ALLOCATION", f"Rejected allocation proposal #{allocation_id}")
        flash(f"Allocation proposal #{allocation_id} REJECTED.", "warning")

    conn.commit()
    conn.close()
    return redirect(url_for("resource.index"))
