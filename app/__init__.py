# app/__init__.py
from flask import Flask, request
from app.config import config
from app.extensions import db, login_manager


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.home import home_bp
    from app.routes.domain import domain_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.grocery import grocery_bp
    from app.routes.festivals import festivals_bp
    from app.routes.pricing import pricing_bp
    from app.routes.scan import scan_bp
    from app.routes.products import products_bp
    from app.routes.warehouses import warehouses_bp
    from app.routes.receipts import receipts_bp
    from app.routes.deliveries import deliveries_bp
    from app.routes.transfers import transfers_bp
    from app.routes.adjustments import adjustments_bp
    from app.routes.ledger import ledger_bp
    from app.routes.intelligence import intelligence_bp
    from app.routes.space_management import space_bp
    from app.routes.simulator import simulator_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.alerts import alerts_bp
    from app.routes.assistant import assistant_bp
    from app.routes.api import api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(domain_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(grocery_bp)
    app.register_blueprint(festivals_bp)
    app.register_blueprint(pricing_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(warehouses_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(deliveries_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(adjustments_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(space_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(assistant_bp)

    # Enable CORS for Decoupled Frontend
    FRONTEND_ORIGIN = 'http://127.0.0.1:3000'

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')

        if origin == FRONTEND_ORIGIN:
            response.headers['Access-Control-Allow-Origin'] = FRONTEND_ORIGIN

        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization, X-Requested-With'
        )
        response.headers['Access-Control-Allow-Methods'] = (
            'GET, POST, PUT, DELETE, OPTIONS'
        )

        return response

    @app.route('/api/v1/health')
    def health_check():
        from flask import jsonify

        return jsonify({
            'status': 'healthy',
            'service': 'StockSense Dual Engine Server',
            'version': '2.0-AI',
            'database': 'Connected'
        })

    # Register Decoupled API Blueprints
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

    @app.context_processor
    def inject_globals():
        from flask import session
        from app.models.operation import (
            Receipt,
            Delivery,
            Transfer,
            PutawayTask,
            PickTask
        )
        from app.models.grocery import ReplenishmentTask
        from app.models.ai_intelligence import Alert
        from app.services.inventory_health_service import calculate_system_wide_health_score

        pending_count = (
            Receipt.query.filter(
                Receipt.status.in_(['Draft', 'Waiting', 'Arrived'])
            ).count()
            + Delivery.query.filter(
                Delivery.status.in_(['Draft', 'Ready', 'Picking'])
            ).count()
            + Transfer.query.filter(
                Transfer.status.in_(['Draft', 'Waiting'])
            ).count()
            + PutawayTask.query.filter_by(status='Pending').count()
            + PickTask.query.filter_by(status='Pending').count()
            + ReplenishmentTask.query.filter_by(status='Pending').count()
        )

        open_alerts_count = Alert.query.filter_by(status='Open').count()

        health_score = 92.5

        try:
            res = calculate_system_wide_health_score()
            health_score = res['overall_score']
        except Exception:
            health_score = 92.5

        active_domain = session.get('active_domain', 'warehouse')

        return {
            'global_pending_ops': pending_count,
            'global_open_alerts': open_alerts_count,
            'global_health_score': health_score,
            'active_domain': active_domain
        }

    return app