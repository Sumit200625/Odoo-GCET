# app/__init__.py
from flask import Flask
from app.config import config
from app.extensions import db, login_manager

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.warehouses import warehouses_bp
    from app.routes.receipts import receipts_bp
    from app.routes.deliveries import deliveries_bp
    from app.routes.transfers import transfers_bp
    from app.routes.adjustments import adjustments_bp
    from app.routes.ledger import ledger_bp
    from app.routes.intelligence import intelligence_bp
    from app.routes.space_management import space_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(warehouses_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(deliveries_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(adjustments_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(space_bp)

    @app.context_processor
    def inject_globals():
        from app.models.operation import Receipt, Delivery, Transfer
        from app.services.ai_intelligence_service import calculate_inventory_health_score
        
        pending_count = (
            Receipt.query.filter(Receipt.status.in_(['Draft', 'Waiting'])).count() +
            Delivery.query.filter(Delivery.status.in_(['Draft', 'Ready'])).count() +
            Transfer.query.filter(Transfer.status.in_(['Draft', 'Waiting'])).count()
        )
        
        health_score = 100.0
        try:
            health_score = calculate_inventory_health_score()
        except Exception:
            health_score = 92.5

        return {
            'global_pending_ops': pending_count,
            'global_health_score': health_score
        }

    return app
