# backend/app/api/pricing_api.py
from flask import Blueprint, jsonify, request
from app.models.product import Product
from app.models.grocery import PriceHistory
from app.services.price_intelligence_service import update_product_price, recommend_near_expiry_markdown

pricing_api_bp = Blueprint('pricing_api', __name__, url_prefix='/api/v1/pricing')

@pricing_api_bp.route('/', methods=['GET'])
def get_pricing_overview():
    products = Product.query.filter_by(is_active=True).all()
    
    markdown_recs = []
    for p in products:
        m_rec = recommend_near_expiry_markdown(p.id)
        if m_rec:
            markdown_recs.append(m_rec)

    histories = PriceHistory.query.order_by(PriceHistory.created_at.desc()).limit(20).all()
    history_list = [{
        'id': h.id,
        'product_name': h.product.name if h.product else f"SKU #{h.product_id}",
        'old_price': h.old_price,
        'new_price': h.new_price,
        'price_type': h.price_type,
        'rationale': h.rationale,
        'timestamp': h.created_at.strftime('%Y-%m-%d %H:%M') if h.created_at else 'N/A'
    } for h in histories]

    prod_list = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'selling_price': p.selling_price,
        'active_price': p.active_price
    } for p in products]

    return jsonify({
        'products': prod_list,
        'markdown_recommendations': markdown_recs,
        'price_history': history_list
    })

@pricing_api_bp.route('/update', methods=['POST'])
def update_price():
    payload = request.get_json() or {}
    prod_id = payload.get('product_id')
    new_price = float(payload.get('new_price'))
    price_type = payload.get('price_type', 'Standard')
    rationale = payload.get('rationale', 'Manager Manual Price Adjustment')
    user_id = payload.get('user_id', 1)

    try:
        update_product_price(prod_id, new_price, price_type, rationale, user_id)
        return jsonify({
            'success': True,
            'message': 'Price update saved successfully. Immutable PriceHistory record logged.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
