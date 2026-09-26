# backend/app/__init__.py
import os
import sys
from flask import Flask, jsonify, request
from flask_login import LoginManager

# Add parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.extensions import db, login_manager
from app.models.user import User

def create_backend_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'stocksense-ai-secret-key-2026')
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'stocksense.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Enable CORS for Decoupled Frontend (Port 3000 -> Port 5000)
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

    @app.route('/api/v1/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'StockSense Decoupled REST API',
            'version': '2.0-AI',
            'database': 'Connected'
        })

    # Register API Blueprints
    from backend.app.api.warehouse_api import warehouse_api_bp
    from backend.app.api.grocery_api import grocery_api_bp
    from backend.app.api.scan_api import scan_api_bp
    from backend.app.api.festival_api import festival_api_bp
    from backend.app.api.pricing_api import pricing_api_bp
    from backend.app.api.simulator_api import simulator_api_bp
    from backend.app.api.assistant_api import assistant_api_bp
    from backend.app.api.auth_api import auth_api_bp

    app.register_blueprint(warehouse_api_bp)
    app.register_blueprint(grocery_api_bp)
    app.register_blueprint(scan_api_bp)
    app.register_blueprint(festival_api_bp)
    app.register_blueprint(pricing_api_bp)
    app.register_blueprint(simulator_api_bp)
    app.register_blueprint(assistant_api_bp)
    app.register_blueprint(auth_api_bp)

    return app
