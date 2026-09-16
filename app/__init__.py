from flask import Flask
from app.db import init_db
import os

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "disaster_management_expert_system_secret_key_2026"

    # Initialize Database Schema & Safe Migrations
    with app.app_context():
        init_db()

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.disaster_routes import disaster_bp
    from app.routes.resource_routes import resource_bp
    from app.routes.gdss_routes import gdss_bp
    from app.routes.cscw_routes import cscw_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(disaster_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(gdss_bp)
    app.register_blueprint(cscw_bp)
    app.register_blueprint(analytics_bp)

    return app
