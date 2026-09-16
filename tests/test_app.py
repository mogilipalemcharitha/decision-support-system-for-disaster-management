import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.expert_system.engine import RuleEngine
from app.db import init_db, get_db

class DisasterSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def test_rule_engine_flood(self):
        engine = RuleEngine()
        flood_input = {
            "people_affected": 1200,
            "medical_emergency": "HIGH",
            "road_status": "BLOCKED",
            "ambulances": 0,
            "hospital_beds": 0,
            "specific_metrics": {"water_level": 3.5, "rainfall": 120, "evacuation_needed": True}
        }
        result = engine.evaluate_area("Flood", flood_input)
        self.assertEqual(result["priority"], "CRITICAL")
        self.assertGreaterEqual(result["score"], 14)
        self.assertGreaterEqual(len(result["triggered_rules"]), 5)
        self.assertGreaterEqual(result["resource_recommendations"]["Ambulances"], 4)

    def test_rule_engine_earthquake(self):
        engine = RuleEngine()
        eq_input = {
            "people_affected": 600,
            "medical_emergency": "MEDIUM",
            "road_status": "ACCESSIBLE",
            "ambulances": 3,
            "hospital_beds": 15,
            "specific_metrics": {"building_damage_pct": 55, "trapped_people": 22}
        }
        result = engine.evaluate_area("Earthquake", eq_input)
        self.assertIn(result["priority"], ["HIGH", "CRITICAL"])

    def test_auth_login(self):
        response = self.client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Dashboard" in response.data or b"Command Center" in response.data)

    def test_unauthorized_access(self):
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_gdss_consensus_calculation(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO disasters (disaster_type, location, created_at) VALUES ('Flood', 'Test Loc', '2026-01-01')")
        did = cursor.lastrowid
        cursor.execute("INSERT INTO gdss_decisions (disaster_id, title, issue_description, status, created_at) VALUES (?, 'Test Choice', 'Desc', 'OPEN', '2026-01-01')", (did,))
        dec_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO gdss_votes (decision_id, user_id, username, role, vote_option, created_at) VALUES (?, 1, 'u1', 'r1', 'Area A', 'now')", (dec_id,))
        cursor.execute("INSERT INTO gdss_votes (decision_id, user_id, username, role, vote_option, created_at) VALUES (?, 2, 'u2', 'r2', 'Area A', 'now')", (dec_id,))
        cursor.execute("INSERT INTO gdss_votes (decision_id, user_id, username, role, vote_option, created_at) VALUES (?, 3, 'u3', 'r3', 'Area A', 'now')", (dec_id,))
        cursor.execute("INSERT INTO gdss_votes (decision_id, user_id, username, role, vote_option, created_at) VALUES (?, 4, 'u4', 'r4', 'Area B', 'now')", (dec_id,))
        conn.commit()

        votes = conn.execute("SELECT vote_option FROM gdss_votes WHERE decision_id = ?", (dec_id,)).fetchall()
        counts = {}
        for v in votes:
            opt = v["vote_option"]
            counts[opt] = counts.get(opt, 0) + 1
        winning = max(counts, key=counts.get)
        pct = (counts[winning] / len(votes)) * 100
        
        self.assertEqual(winning, "Area A")
        self.assertEqual(pct, 75.0)
        conn.close()

if __name__ == "__main__":
    unittest.main()
