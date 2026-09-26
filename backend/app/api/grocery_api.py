# backend/app/api/grocery_api.py
from flask import Blueprint, jsonify, request
from app.models.product import Product
from app.models.grocery import Store, WasteRecord, POSSale
from app.services.grocery_intelligence_service import (
    get_grocery_dashboard_data,
    record_pos_checkout_sale,
    record_waste_disposal
)

grocery_api_bp = Blueprint('grocery_api', __name__, url_prefix='/api/v1/grocery')

@grocery_api_bp.route('/dashboard', methods=['GET'])
def dashboard_data():
    store_id = request.args.get('store_id', type=int, default=1)
    data = get_grocery_dashboard_data(store_id=store_id)
    return jsonify(data)

@grocery_api_bp.route('/inventory', methods=['GET'])
def inventory_list():
    products = Product.query.filter_by(is_active=True).all()
    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'barcode': p.barcode or 'N/A',
        'selling_price': p.selling_price,
        'active_price': p.active_price,
        'shelf_stock': p.shelf_stock,
        'backroom_stock': p.backroom_stock,
        'shelf_capacity': p.shelf_capacity,
        'is_perishable': p.is_perishable,
        'total_stock': p.total_stock
    } for p in products]
    return jsonify({'products': data})

@grocery_api_bp.route('/pos/checkout', methods=['POST'])
def pos_checkout():
    payload = request.get_json() or {}
    store_id = payload.get('store_id', 1)
    items = payload.get('items', [])
    user_id = payload.get('user_id', 1)

    try:
        sale = record_pos_checkout_sale(store_id, items, user_id)
        return jsonify({
            'success': True,
            'receipt_number': sale.receipt_number,
            'total_amount': sale.total_amount,
            'message': 'POS Checkout completed successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@grocery_api_bp.route('/waste', methods=['GET', 'POST'])
def waste_management():
    if request.method == 'POST':
        payload = request.get_json() or {}
        prod_id = payload.get('product_id')
        qty = float(payload.get('quantity', 1.0))
        reason = payload.get('reason', 'Expired')
        user_id = payload.get('user_id', 1)

        try:
            w = record_waste_disposal(prod_id, qty, reason, user_id)
            return jsonify({
                'success': True,
                'record_code': w.record_code,
                'total_cost_waste': w.total_cost_waste,
                'message': 'Waste record logged and inventory updated'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    records = WasteRecord.query.order_by(WasteRecord.created_at.desc()).all()
    rec_data = [{
        'id': r.id,
        'record_code': r.record_code,
        'product_name': r.product.name if r.product else f"SKU #{r.product_id}",
        'quantity': r.quantity,
        'total_cost_waste': r.total_cost_waste,
        'reason': r.reason,
        'timestamp': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else 'N/A'
    } for r in records]
    return jsonify({'records': rec_data})
