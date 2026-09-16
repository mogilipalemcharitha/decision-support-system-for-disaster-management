import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "disaster.db")

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Preserve/Update Existing 'disasters' table
    cursor.execute("""
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

    # Check if 'status' column exists in disasters table, if not add it
    cursor.execute("PRAGMA table_info(disasters)")
    columns = [col[1] for col in cursor.fetchall()]
    if "status" not in columns:
        cursor.execute("ALTER TABLE disasters ADD COLUMN status TEXT DEFAULT 'ACTIVE'")

    # 2. Preserve/Update Existing 'stakeholders' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # 3. Preserve/Update Existing 'messages' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stakeholder TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # 4. Users Table (Role-based authentication)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # 5. Affected Sub-Areas Table (Multi-area prioritization)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS affected_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_id INTEGER NOT NULL,
            area_name TEXT NOT NULL,
            people_affected INTEGER DEFAULT 0,
            medical_emergency TEXT DEFAULT 'LOW',
            road_status TEXT DEFAULT 'ACCESSIBLE',
            specific_metrics_json TEXT,
            calculated_priority TEXT DEFAULT 'LOW',
            reasoning_json TEXT,
            created_at TEXT,
            FOREIGN KEY (disaster_id) REFERENCES disasters(id) ON DELETE CASCADE
        )
    """)

    # 6. Resources Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            location TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            assigned_disaster_id INTEGER,
            assigned_area_id INTEGER,
            last_updated_time TEXT
        )
    """)

    # 7. Resource Allocation Proposals Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_id INTEGER NOT NULL,
            area_id INTEGER,
            resource_type TEXT NOT NULL,
            recommended_qty INTEGER NOT NULL,
            approved_qty INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'PENDING',
            requested_by TEXT,
            approved_by TEXT,
            updated_at TEXT,
            FOREIGN KEY (disaster_id) REFERENCES disasters(id) ON DELETE CASCADE
        )
    """)

    # 8. GDSS Decisions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gdss_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            expert_recommendation TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN',
            final_decision TEXT,
            finalized_by TEXT,
            created_at TEXT,
            FOREIGN KEY (disaster_id) REFERENCES disasters(id) ON DELETE CASCADE
        )
    """)

    # 9. GDSS Stakeholder Opinions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gdss_opinions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            opinion_text TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (decision_id) REFERENCES gdss_decisions(id) ON DELETE CASCADE
        )
    """)

    # 10. GDSS Stakeholder Votes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gdss_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            vote_option TEXT NOT NULL,
            created_at TEXT,
            UNIQUE(decision_id, user_id),
            FOREIGN KEY (decision_id) REFERENCES gdss_decisions(id) ON DELETE CASCADE
        )
    """)

    # 11. Alerts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # 12. Activity Audit Log Table (CSCW timeline)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()

    # Seed Default Roles & Demo Accounts if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("admin", "admin123", "System Administrator", "Admin System Controller"),
            ("authority", "auth123", "Disaster Management Authority", "Commander Chief Authority"),
            ("police", "police123", "Police", "Chief Inspector Officer"),
            ("fire", "fire123", "Fire & Rescue", "Captain Rescue Officer"),
            ("medical", "med123", "Medical/Ambulance Team", "Chief Medical Responder"),
            ("hospital", "hosp123", "Hospital", "Dr. Emergency Director"),
            ("ngo", "ngo123", "NGO/Volunteer", "Relief Coordinator NGO")
        ]
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for username, password, role, full_name in demo_users:
            pass_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, pass_hash, role, full_name, now_str))
        conn.commit()

    # Seed Sample Initial Resources if empty
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_resources = [
            ("Rapid Ambulance Unit A", "Ambulances", 12, "Central Depot", "Available"),
            ("National Rescue Squad 1", "Rescue teams", 5, "North Hub", "Available"),
            ("Hazmat Fire Truck Delta", "Fire engines", 4, "Station 3", "Available"),
            ("Mobile Trauma Medical Kit", "Medical teams", 8, "City Base", "Available"),
            ("ICU Bed Unit - City Hospital", "Hospital beds", 45, "City Hospital", "Available"),
            ("Emergency Rations Pack", "Food packets", 1500, "Relief Warehouse", "Available"),
            ("Clean Water Tanker 5K Liters", "Drinking water", 20, "Water Supply Hub", "Available"),
            ("Temp Relief Camp Shelter A", "Shelters", 3, "East Stadium", "Available"),
            ("Heavy Hydraulic Cutter Kit", "Rescue equipment", 10, "Equipment Armory", "Available")
        ]
        for name, rtype, qty, loc, status in sample_resources:
            cursor.execute("""
                INSERT INTO resources (name, resource_type, quantity, location, status, last_updated_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, rtype, qty, loc, status, now_str))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
