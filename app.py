from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "disaster.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # Disaster information table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS disasters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_type TEXT NOT NULL,
            location TEXT NOT NULL,
            people_affected INTEGER,
            medical_emergency TEXT,
            road_status TEXT,
            available_ambulances INTEGER,
            hospital_beds INTEGER,
            priority TEXT,
            recommendation TEXT,
            created_at TEXT
        )
    """)

    # Stakeholders table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Messages for CSCW collaboration
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stakeholder TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# EXPERT SYSTEM
# =========================================================

def expert_system(people_affected,
                  medical_emergency,
                  road_status,
                  ambulances,
                  hospital_beds):

    score = 0
    reasons = []

    # Rule 1: Number of affected people
    if people_affected >= 1000:
        score += 4
        reasons.append("More than 1000 people are affected.")

    elif people_affected >= 500:
        score += 3
        reasons.append("More than 500 people are affected.")

    elif people_affected >= 100:
        score += 2
        reasons.append("More than 100 people are affected.")

    else:
        score += 1
        reasons.append("Less than 100 people are affected.")

    # Rule 2: Medical emergency
    if medical_emergency == "HIGH":
        score += 4
        reasons.append("Medical emergency level is HIGH.")

    elif medical_emergency == "MEDIUM":
        score += 2
        reasons.append("Medical emergency level is MEDIUM.")

    else:
        score += 1
        reasons.append("Medical emergency level is LOW.")

    # Rule 3: Road condition
    if road_status == "BLOCKED":
        score += 1
        reasons.append("Road is blocked, making rescue difficult.")

    else:
        score += 2
        reasons.append("Road is accessible for rescue teams.")

    # Rule 4: Ambulance availability
    if ambulances == 0:
        score += 3
        reasons.append("No ambulances are currently available.")

    elif ambulances <= 2:
        score += 2
        reasons.append("Only a small number of ambulances are available.")

    # Rule 5: Hospital capacity
    if hospital_beds == 0:
        score += 3
        reasons.append("No hospital beds are available.")

    elif hospital_beds <= 10:
        score += 2
        reasons.append("Hospital bed availability is low.")

    # Determine priority
    if score >= 13:
        priority = "CRITICAL"

    elif score >= 9:
        priority = "HIGH"

    elif score >= 6:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    # Generate recommendation
    if priority == "CRITICAL":
        recommendation = (
            "Immediate rescue operation required. "
            "Deploy available rescue teams and ambulances. "
            "Coordinate with nearby hospitals immediately."
        )

    elif priority == "HIGH":
        recommendation = (
            "High priority response required. "
            "Send rescue teams and arrange medical support."
        )

    elif priority == "MEDIUM":
        recommendation = (
            "Monitor the situation and prepare rescue and medical resources."
        )

    else:
        recommendation = (
            "Continue monitoring the area and keep emergency resources ready."
        )

    return priority, recommendation, reasons


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# DISASTER ANALYSIS
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    disaster_type = request.form["disaster_type"]
    location = request.form["location"]

    people_affected = int(request.form["people_affected"])

    medical_emergency = request.form["medical_emergency"]

    road_status = request.form["road_status"]

    ambulances = int(request.form["ambulances"])

    hospital_beds = int(request.form["hospital_beds"])

    # Run Expert System
    priority, recommendation, reasons = expert_system(
        people_affected,
        medical_emergency,
        road_status,
        ambulances,
        hospital_beds
    )

    # Save result to database
    conn = get_db()

    conn.execute("""
        INSERT INTO disasters
        (
            disaster_type,
            location,
            people_affected,
            medical_emergency,
            road_status,
            available_ambulances,
            hospital_beds,
            priority,
            recommendation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        disaster_type,
        location,
        people_affected,
        medical_emergency,
        road_status,
        ambulances,
        hospital_beds,
        priority,
        recommendation,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        disaster_type=disaster_type,
        location=location,
        priority=priority,
        recommendation=recommendation,
        reasons=reasons
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    conn = get_db()

    disasters = conn.execute("""
        SELECT * FROM disasters
        ORDER BY id DESC
    """).fetchall()

    messages = conn.execute("""
        SELECT * FROM messages
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        disasters=disasters,
        messages=messages
    )


# =========================================================
# CSCW - SEND MESSAGE
# =========================================================

@app.route("/message", methods=["POST"])
def message():

    stakeholder = request.form["stakeholder"]
    message = request.form["message"]

    conn = get_db()

    conn.execute("""
        INSERT INTO messages
        (stakeholder, message, created_at)
        VALUES (?, ?, ?)
    """, (
        stakeholder,
        message,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )