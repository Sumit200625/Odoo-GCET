# app/routes/suppliers.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.models.supplier import Supplier
from app.models.product import Product
from app.services.supplier_intelligence_service import evaluate_all_suppliers, rank_suppliers_for_po

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@suppliers_bp.route('/')
@login_required
def index():
    suppliers_data = evaluate_all_suppliers()
    products = Product.query.filter_by(is_active=True).all()
    
    selected_prod_id = request.args.get('product_id', type=int) or (products[0].id if products else None)
    objective = request.args.get('objective', 'Balanced')
    
    rankings = []
    if selected_prod_id:
        prod = Product.query.get(selected_prod_id)
        rankings = rank_suppliers_for_po(prod, objective=objective)

    return render_template(
        'suppliers/index.html',
        suppliers=suppliers_data,
        products=products,
        selected_prod_id=selected_prod_id,
        objective=objective,
        rankings=rankings
    )
