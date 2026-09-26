# app/routes/grocery.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.grocery import Store, WasteRecord, POSSale
from app.services.grocery_intelligence_service import (
    get_grocery_dashboard_data,
    record_pos_checkout_sale,
    record_waste_disposal
)

grocery_bp = Blueprint('grocery', __name__, url_prefix='/grocery')

@grocery_bp.route('/')
@grocery_bp.route('/dashboard')
@login_required
def dashboard():
    store_id = request.args.get('store_id', type=int, default=1)
    data = get_grocery_dashboard_data(store_id=store_id)
    return render_template('grocery/dashboard.html', data=data)

@grocery_bp.route('/inventory')
@login_required
def inventory():
    products = Product.query.filter_by(is_active=True).all()
    return render_template('grocery/inventory.html', products=products)

@grocery_bp.route('/pos', methods=['GET', 'POST'])
@login_required
def pos_checkout():
    products = Product.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            prod_id = int(request.form.get('product_id'))
            qty = float(request.form.get('quantity', 1.0))
            items = [{'product_id': prod_id, 'quantity': qty}]
            
            sale = record_pos_checkout_sale(1, items, current_user.id)
            flash(f"POS Sale Checkout completed! Receipt #{sale.receipt_number}. Shelf stock updated and auto-replenishment checked.", "success")
        except Exception as e:
            flash(f"Checkout failed: {str(e)}", "danger")
        return redirect(url_for('grocery.pos_checkout'))

    recent_sales = POSSale.query.order_by(POSSale.created_at.desc()).limit(10).all()
    return render_template('grocery/pos.html', products=products, recent_sales=recent_sales)

@grocery_bp.route('/waste', methods=['GET', 'POST'])
@login_required
def waste_management():
    products = Product.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            prod_id = int(request.form.get('product_id'))
            qty = float(request.form.get('quantity', 1.0))
            reason = request.form.get('reason', 'Expired')
            
            w = record_waste_disposal(prod_id, qty, reason, current_user.id)
            flash(f"Waste Record #{w.record_code} logged (${w.total_cost_waste}). Stock adjusted.", "warning")
        except Exception as e:
            flash(f"Waste logging failed: {str(e)}", "danger")
        return redirect(url_for('grocery.waste_management'))

    records = WasteRecord.query.order_by(WasteRecord.created_at.desc()).all()
    return render_template('grocery/waste.html', products=products, records=records)
