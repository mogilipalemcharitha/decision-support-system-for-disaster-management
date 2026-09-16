# Disaster-Management Knowledge Base Rules
# Rules are modular, transparent, and categorized.

DEFAULT_RULES = {
    "POPULATION": [
        {"id": "POP_CRIT", "threshold": 1000, "points": 4, "msg": "Large population affected (>= 1,000 people). High human exposure."},
        {"id": "POP_HIGH", "threshold": 500, "points": 3, "msg": "Significant population affected (>= 500 people)."},
        {"id": "POP_MED", "threshold": 100, "points": 2, "msg": "Moderate population affected (>= 100 people)."},
        {"id": "POP_LOW", "threshold": 0, "points": 1, "msg": "Local population affected (< 100 people)."}
    ],

    "MEDICAL": [
        {"id": "MED_HIGH", "level": "HIGH", "points": 4, "msg": "Critical medical emergency reported. Immediate life threat."},
        {"id": "MED_MED", "level": "MEDIUM", "points": 2, "msg": "Moderate medical emergency level reported."},
        {"id": "MED_LOW", "level": "LOW", "points": 1, "msg": "Low medical emergency level."}
    ],

    "ROAD": [
        {"id": "ROAD_BLOCKED", "status": "BLOCKED", "points": 3, "msg": "Road access is BLOCKED. Alternate routing and clearing required."},
        {"id": "ROAD_PARTIAL", "status": "PARTIAL", "points": 2, "msg": "Road access is PARTIALLY BLOCKED. Heavy vehicles restricted."},
        {"id": "ROAD_OK", "status": "ACCESSIBLE", "points": 1, "msg": "Road is ACCESSIBLE for rescue and relief teams."}
    ],

    "AMBULANCE": [
        {"id": "AMB_CRIT", "max_qty": 0, "points": 3, "msg": "Zero ambulances available. Critical transport shortage!"},
        {"id": "AMB_LOW", "max_qty": 2, "points": 2, "msg": "Ambulance availability is critically low (<= 2)."},
        {"id": "AMB_OK", "max_qty": 999, "points": 1, "msg": "Ambulance supply is currently stable."}
    ],

    "HOSPITAL_BEDS": [
        {"id": "BED_CRIT", "max_qty": 0, "points": 3, "msg": "Zero hospital beds available! Patient diversion required."},
        {"id": "BED_LOW", "max_qty": 10, "points": 2, "msg": "Hospital bed capacity is near exhaustion (<= 10 beds)."},
        {"id": "BED_OK", "max_qty": 999, "points": 1, "msg": "Hospital bed capacity is adequate."}
    ]
}

# Disaster-Specific Rules Engine Configurations
DISASTER_SPECIFIC_KNOWLEDGE = {
    "Flood": {
        "water_level": [
            {"min": 3.0, "points": 4, "msg": "Dangerous flood water level (>= 3.0 m above danger mark). Inundation critical."},
            {"min": 1.5, "points": 2, "msg": "Moderate flood water level (>= 1.5 m)."}
        ],
        "rainfall": [
            {"min": 100, "points": 3, "msg": "Heavy torrential rainfall (>= 100 mm/hr). Flash flood alert."},
            {"min": 50, "points": 2, "msg": "Moderate heavy rainfall (>= 50 mm/hr)."}
        ],
        "evacuation_needed": [
            {"value": True, "points": 3, "msg": "Immediate population evacuation required due to rising water."}
        ]
    },

    "Earthquake": {
        "building_damage_pct": [
            {"min": 50, "points": 4, "msg": "Severe structural collapse (>= 50% buildings damaged/collapsed)."},
            {"min": 20, "points": 2, "msg": "Moderate structural damage reported (>= 20%)."}
        ],
        "trapped_people": [
            {"min": 20, "points": 4, "msg": "High number of trapped victims under rubble (>= 20 trapped). Search & rescue critical!"},
            {"min": 5, "points": 2, "msg": "Trapped victims reported (>= 5 trapped)."}
        ],
        "structural_risk": [
            {"level": "CRITICAL", "points": 3, "msg": "High aftershock and secondary structural collapse hazard."}
        ]
    },

    "Cyclone": {
        "wind_speed_kmh": [
            {"min": 150, "points": 4, "msg": "Severe Category Cyclone wind speed (>= 150 km/h). Severe destruction hazard."},
            {"min": 90, "points": 2, "msg": "High cyclone wind speed (>= 90 km/h)."}
        ],
        "coastal_surge_risk": [
            {"level": "HIGH", "points": 3, "msg": "High coastal storm surge risk. Coastal inundation imminent."}
        ],
        "shelter_capacity_shortfall": [
            {"value": True, "points": 2, "msg": "Emergency cyclone shelters reaching maximum capacity."}
        ]
    },

    "Fire": {
        "fire_severity": [
            {"level": "CRITICAL", "points": 4, "msg": "Uncontrolled wildfire/structural inferno. Extreme heat and rapid spread."},
            {"level": "HIGH", "points": 3, "msg": "High intensity fire spreading across structures."}
        ],
        "smoke_hazard": [
            {"level": "HIGH", "points": 3, "msg": "Toxic smoke hazard level HIGH. Respiratory protection and evacuation required."}
        ],
        "trapped_people": [
            {"min": 1, "points": 3, "msg": "People trapped inside burning structures! Immediate fire rescue required."}
        ]
    },

    "Landslide": {
        "terrain_risk": [
            {"level": "HIGH", "points": 4, "msg": "Unstable steep terrain slope with active mudslide hazard."},
            {"level": "MEDIUM", "points": 2, "msg": "Moderate landslide terrain risk."}
        ],
        "road_blockage_pct": [
            {"min": 80, "points": 3, "msg": "Severe road blockage (>= 80% blocked by debris). Heavy earthmovers needed."}
        ],
        "trapped_people": [
            {"min": 1, "points": 3, "msg": "Victims buried/trapped by debris flow."}
        ]
    }
}
