# app/routes/ledger.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.services.ledger_service import get_filtered_ledger
from app.models.product import Product
from app.models.warehouse import Location

ledger_bp = Blueprint('ledger', __name__, url_prefix='/ledger')

@ledger_bp.route('')
@login_required
def index():
    product_id = request.args.get('product_id', type=int)
    location_id = request.args.get('location_id', type=int)
    operation_type = request.args.get('operation_type', '').strip()
    search = request.args.get('search', '').strip()

    entries = get_filtered_ledger(
        product_id=product_id,
        location_id=location_id,
        operation_type=operation_type,
        search=search,
        limit=150
    )

    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    locations = Location.query.all()

    return render_template(
        'ledger/index.html',
        entries=entries,
        products=products,
        locations=locations,
        selected_product_id=product_id,
        selected_location_id=location_id,
        selected_op_type=operation_type,
        search=search
    )
