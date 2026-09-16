from flask import Blueprint, request, redirect, url_for, session, flash
from app.db import get_db
from app.models import log_activity
from app.routes.auth_routes import login_required
from datetime import datetime

cscw_bp = Blueprint("cscw", __name__)

@cscw_bp.route("/message", methods=["POST"])
@login_required
def send_message():
    stakeholder = request.form.get("stakeholder") or session.get("role")
    message_text = request.form.get("message")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        INSERT INTO messages (stakeholder, message, created_at)
        VALUES (?, ?, ?)
    """, (f"{session.get('full_name')} ({stakeholder})", message_text, now_str))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "SEND_CSCW_MESSAGE", f"Posted update: {message_text[:40]}...")
    flash("Team update broadcasted.", "success")
    return redirect(url_for("disaster.dashboard"))

@cscw_bp.route("/alerts/<int:alert_id>/ack", methods=["POST"])
@login_required
def acknowledge_alert(alert_id):
    conn = get_db()
    conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "ACK_ALERT", f"Acknowledged alert #{alert_id}")
    flash("Alert acknowledged.", "info")
    return redirect(url_for("disaster.dashboard"))
