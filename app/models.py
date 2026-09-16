from app.db import get_db
from datetime import datetime
import json

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def log_activity(user_id, username, role, action, details=""):
    conn = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO activity_logs (user_id, username, role, action, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, role, action, details, now_str))
    conn.commit()
    conn.close()

def create_alert(severity, title, message):
    conn = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO alerts (severity, title, message, acknowledged, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (severity, title, message, now_str))
    conn.commit()
    conn.close()

def get_all_disasters():
    conn = get_db()
    disasters = conn.execute("SELECT * FROM disasters ORDER BY id DESC").fetchall()
    conn.close()
    return disasters

def get_disaster_by_id(disaster_id):
    conn = get_db()
    disaster = conn.execute("SELECT * FROM disasters WHERE id = ?", (disaster_id,)).fetchone()
    conn.close()
    return disaster

def get_affected_areas_by_disaster(disaster_id):
    conn = get_db()
    areas = conn.execute("SELECT * FROM affected_areas WHERE disaster_id = ? ORDER BY id ASC", (disaster_id,)).fetchall()
    conn.close()
    return areas

def get_all_resources():
    conn = get_db()
    resources = conn.execute("SELECT * FROM resources ORDER BY id ASC").fetchall()
    conn.close()
    return resources

def get_unacknowledged_alerts():
    conn = get_db()
    alerts = conn.execute("SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY id DESC").fetchall()
    conn.close()
    return alerts

def get_recent_activity_logs(limit=20):
    conn = get_db()
    logs = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return logs
