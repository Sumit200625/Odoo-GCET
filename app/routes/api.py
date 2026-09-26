# app/routes/api.py
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models.product import Product
from app.models.warehouse import Warehouse, Location
from app.models.stock import StockBalance
from app.models.ledger import StockLedger
from app.models.supplier import Supplier
from app.services.inventory_ledger_service import get_unified_inventory_summary
from app.services.forecasting_engine import generate_ai_forecast_for_sku
from app.services.predictive_risk_engine import run_predictive_risk_assessment

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/inventory/summary')
@login_required
def inventory_summary():
    prod_id = request.args.get('product_id', type=int)
    wh_id = request.args.get('warehouse_id', type=int)
    res = get_unified_inventory_summary(prod_id, wh_id)
    return jsonify({'status': 'success', 'data': res})

@api_bp.route('/products')
@login_required
def list_products():
    products = Product.query.filter_by(is_active=True).all()
    data = [{
        'id': p.id,
        'sku': p.sku,
        'name': p.name,
        'unit': p.unit,
        'unit_cost': p.unit_cost,
        'total_stock': p.total_stock,
        'reorder_level': p.reorder_level,
        'abc_class': p.abc_class,
        'xyz_class': p.xyz_class,
        'velocity': p.velocity_class
    } for p in products]
    return jsonify({'status': 'success', 'count': len(data), 'data': data})

@api_bp.route('/forecast/<int:product_id>')
@login_required
def sku_forecast(product_id):
    fc = generate_ai_forecast_for_sku(product_id)
    return jsonify({'status': 'success', 'data': fc})

@api_bp.route('/risks')
@login_required
def active_risks():
    risks = run_predictive_risk_assessment()
    data = [{
        'code': r.risk_code,
        'category': r.risk_category,
        'severity': r.severity,
        'score': r.risk_score,
        'financial_impact': r.financial_impact,
        'mitigation': r.recommended_mitigation
    } for r in risks]
    return jsonify({'status': 'success', 'count': len(data), 'data': data})
