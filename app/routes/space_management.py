# app/routes/space_management.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models.product import Product
from app.services.warehouse_intelligence_service import (
    get_warehouse_space_utilization,
    recommend_smart_putaway,
    get_expiry_and_aging_analysis,
    get_outbound_picking_priorities,
    recommend_fefo_picking
)

space_bp = Blueprint('space_management', __name__, url_prefix='/space-management')

@space_bp.route('')
@login_required
def index():
    # 1. Space Utilization Matrix
    space_matrix = get_warehouse_space_utilization()

    # 2. Expiry & Aging FEFO Alerts
    expiry_alerts = get_expiry_and_aging_analysis(days_threshold=60)

    # 3. Outbound Picking Priority Queue
    picking_queue = get_outbound_picking_priorities()

    products = Product.query.filter_by(is_active=True).all()

    return render_template(
        'space_management/index.html',
        space_matrix=space_matrix,
        expiry_alerts=expiry_alerts,
        picking_queue=picking_queue,
        products=products
    )

@space_bp.route('/api/put-away')
@login_required
def api_smart_putaway():
    product_id = request.args.get('product_id', type=int)
    quantity = request.args.get('quantity', type=float, default=10.0)

    if not product_id:
        return jsonify({'recommendations': []})

    recs = recommend_smart_putaway(product_id, quantity)
    formatted = [{
        'location_name': r['location'].full_name,
        'location_code': r['location'].code,
        'zone': r['location'].zone,
        'available_capacity': r['available_capacity'],
        'occupancy_pct': r['occupancy_pct'],
        'reason': r['reason']
    } for r in recs]

    return jsonify({'recommendations': formatted})

@space_bp.route('/api/fefo-picking')
@login_required
def api_fefo_picking():
    product_id = request.args.get('product_id', type=int)
    location_id = request.args.get('location_id', type=int)
    quantity = request.args.get('quantity', type=float, default=1.0)

    if not product_id or not location_id:
        return jsonify({'picks': [], 'fulfilled': False})

    res = recommend_fefo_picking(product_id, location_id, quantity)
    return jsonify(res)
