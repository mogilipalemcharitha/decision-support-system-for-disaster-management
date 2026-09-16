from app.expert_system.knowledge_base import DEFAULT_RULES, DISASTER_SPECIFIC_KNOWLEDGE
import json

class RuleEngine:
    """
    Modular, transparent forward-chaining Rule Engine for Disaster Management Expert System.
    Provides explainable priority calculations, rule execution traces, and resource recommendations.
    """

    def evaluate_area(self, disaster_type, area_data):
        """
        area_data expects a dict containing:
        - area_name (str)
        - people_affected (int)
        - medical_emergency (str: LOW, MEDIUM, HIGH)
        - road_status (str: ACCESSIBLE, PARTIAL, BLOCKED)
        - ambulances (int)
        - hospital_beds (int)
        - specific_metrics (dict, optional extra metrics depending on disaster_type)
        """
        score = 0
        triggered_rules = []
        reasons = []

        people_affected = int(area_data.get("people_affected", 0))
        medical_emergency = str(area_data.get("medical_emergency", "LOW")).upper()
        road_status = str(area_data.get("road_status", "ACCESSIBLE")).upper()
        ambulances = int(area_data.get("ambulances", 0))
        hospital_beds = int(area_data.get("hospital_beds", 0))
        specific_metrics = area_data.get("specific_metrics", {})
        if isinstance(specific_metrics, str):
            try:
                specific_metrics = json.loads(specific_metrics)
            except Exception:
                specific_metrics = {}

        # 1. Population Rule Evaluation
        for rule in DEFAULT_RULES["POPULATION"]:
            if people_affected >= rule["threshold"]:
                score += rule["points"]
                triggered_rules.append({"id": rule["id"], "category": "POPULATION", "points": rule["points"], "msg": rule["msg"]})
                reasons.append(rule["msg"])
                break

        # 2. Medical Rule Evaluation
        for rule in DEFAULT_RULES["MEDICAL"]:
            if medical_emergency == rule["level"]:
                score += rule["points"]
                triggered_rules.append({"id": rule["id"], "category": "MEDICAL", "points": rule["points"], "msg": rule["msg"]})
                reasons.append(rule["msg"])
                break

        # 3. Road Status Rule Evaluation
        for rule in DEFAULT_RULES["ROAD"]:
            if road_status == rule["status"]:
                score += rule["points"]
                triggered_rules.append({"id": rule["id"], "category": "ROAD", "points": rule["points"], "msg": rule["msg"]})
                reasons.append(rule["msg"])
                break

        # 4. Ambulance Availability Rule Evaluation
        for rule in DEFAULT_RULES["AMBULANCE"]:
            if ambulances <= rule["max_qty"]:
                score += rule["points"]
                triggered_rules.append({"id": rule["id"], "category": "AMBULANCE", "points": rule["points"], "msg": rule["msg"]})
                reasons.append(rule["msg"])
                break

        # 5. Hospital Bed Availability Rule Evaluation
        for rule in DEFAULT_RULES["HOSPITAL_BEDS"]:
            if hospital_beds <= rule["max_qty"]:
                score += rule["points"]
                triggered_rules.append({"id": rule["id"], "category": "HOSPITAL_BEDS", "points": rule["points"], "msg": rule["msg"]})
                reasons.append(rule["msg"])
                break

        # 6. Disaster-Specific Knowledge Rule Evaluation
        if disaster_type in DISASTER_SPECIFIC_KNOWLEDGE:
            know = DISASTER_SPECIFIC_KNOWLEDGE[disaster_type]

            # Flood specific
            if disaster_type == "Flood":
                wl = float(specific_metrics.get("water_level", 0.0))
                for rule in know.get("water_level", []):
                    if wl >= rule["min"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "FLD_WL", "category": "FLOOD", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

                rf = float(specific_metrics.get("rainfall", 0.0))
                for rule in know.get("rainfall", []):
                    if rf >= rule["min"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "FLD_RF", "category": "FLOOD", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

                if specific_metrics.get("evacuation_needed"):
                    r = know["evacuation_needed"][0]
                    score += r["points"]
                    triggered_rules.append({"id": "FLD_EVAC", "category": "EVACUATION", "points": r["points"], "msg": r["msg"]})
                    reasons.append(r["msg"])

            # Earthquake specific
            elif disaster_type == "Earthquake":
                bd = float(specific_metrics.get("building_damage_pct", 0.0))
                for rule in know.get("building_damage_pct", []):
                    if bd >= rule["min"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "EQ_BD", "category": "EARTHQUAKE", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

                tp = int(specific_metrics.get("trapped_people", 0))
                for rule in know.get("trapped_people", []):
                    if tp >= rule["min"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "EQ_TRAP", "category": "EARTHQUAKE", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

            # Cyclone specific
            elif disaster_type == "Cyclone":
                ws = float(specific_metrics.get("wind_speed_kmh", 0.0))
                for rule in know.get("wind_speed_kmh", []):
                    if ws >= rule["min"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "CYC_WS", "category": "CYCLONE", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

                if str(specific_metrics.get("coastal_surge_risk", "")).upper() == "HIGH":
                    r = know["coastal_surge_risk"][0]
                    score += r["points"]
                    triggered_rules.append({"id": "CYC_SURGE", "category": "CYCLONE", "points": r["points"], "msg": r["msg"]})
                    reasons.append(r["msg"])

            # Fire specific
            elif disaster_type == "Fire":
                fs = str(specific_metrics.get("fire_severity", "")).upper()
                for rule in know.get("fire_severity", []):
                    if fs == rule["level"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "FIR_SEV", "category": "FIRE", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

                if str(specific_metrics.get("smoke_hazard", "")).upper() == "HIGH":
                    r = know["smoke_hazard"][0]
                    score += r["points"]
                    triggered_rules.append({"id": "FIR_SMK", "category": "FIRE", "points": r["points"], "msg": r["msg"]})
                    reasons.append(r["msg"])

            # Landslide specific
            elif disaster_type == "Landslide":
                tr = str(specific_metrics.get("terrain_risk", "")).upper()
                for rule in know.get("terrain_risk", []):
                    if tr == rule["level"]:
                        score += rule["points"]
                        triggered_rules.append({"id": "LS_TR", "category": "LANDSLIDE", "points": rule["points"], "msg": rule["msg"]})
                        reasons.append(rule["msg"])
                        break

        # Priority Mapping
        if score >= 14:
            priority = "CRITICAL"
        elif score >= 10:
            priority = "HIGH"
        elif score >= 6:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Calculate Recommended Resource Allocation Counts
        rec_ambulances = 0
        rec_rescue_teams = 0
        rec_fire_engines = 0
        rec_hospital_beds = 0
        rec_food_packets = 0
        rec_shelters = 0

        if priority == "CRITICAL":
            rec_ambulances = max(4, int(people_affected / 200))
            rec_rescue_teams = max(3, int(people_affected / 300))
            rec_hospital_beds = max(20, int(people_affected / 15))
            rec_food_packets = max(500, people_affected * 2)
            rec_shelters = max(2, int(people_affected / 500))
            if disaster_type == "Fire":
                rec_fire_engines = 4
            elif disaster_type in ["Flood", "Landslide"]:
                rec_rescue_teams += 2
            text_recommendation = (
                "IMMEDIATE CRITICAL EMERGENCY RESPONSE: Deploy rapid rescue squads and ambulances. "
                "Prepare emergency hospital trauma wards and initiate immediate regional evacuation."
            )
        elif priority == "HIGH":
            rec_ambulances = max(2, int(people_affected / 400))
            rec_rescue_teams = max(2, int(people_affected / 500))
            rec_hospital_beds = max(10, int(people_affected / 30))
            rec_food_packets = max(200, people_affected)
            rec_shelters = 1
            if disaster_type == "Fire":
                rec_fire_engines = 2
            text_recommendation = (
                "HIGH PRIORITY ACTION: Dispatch designated emergency response units, clear priority supply routes, "
                "and alert nearest hospital facilities."
            )
        elif priority == "MEDIUM":
            rec_ambulances = 1
            rec_rescue_teams = 1
            rec_hospital_beds = 5
            rec_food_packets = max(50, people_affected)
            rec_shelters = 0
            text_recommendation = "MEDIUM PRIORITY: Monitor area developments, maintain standby medical teams, and prepare relief supplies."
        else:
            rec_ambulances = 0
            rec_rescue_teams = 0
            rec_hospital_beds = 0
            rec_food_packets = 0
            rec_shelters = 0
            text_recommendation = "LOW PRIORITY: Routine monitoring advised. No emergency resource deployment required at present."

        resource_recommendations = {
            "Ambulances": rec_ambulances,
            "Rescue teams": rec_rescue_teams,
            "Fire engines": rec_fire_engines,
            "Hospital beds": rec_hospital_beds,
            "Food packets": rec_food_packets,
            "Shelters": rec_shelters
        }

        return {
            "priority": priority,
            "score": score,
            "triggered_rules": triggered_rules,
            "reasons": reasons,
            "text_recommendation": text_recommendation,
            "resource_recommendations": resource_recommendations
        }
