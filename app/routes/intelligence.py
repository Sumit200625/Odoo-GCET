# app/routes/intelligence.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product
from app.models.warehouse import Location
from app.models.operation import Receipt, ReceiptLine
from app.services.ai_intelligence_service import (
    get_smart_reorder_recommendation,
    get_sku_classification,
    calculate_inventory_health_score,
    get_ai_demand_forecast
)
from app.services.warehouse_intelligence_service import get_supplier_intelligence
from app.utils.rbac import role_required

intelligence_bp = Blueprint('intelligence', __name__, url_prefix='/intelligence')

@intelligence_bp.route('')
@login_required
def index():
    products = Product.query.filter_by(is_active=True).all()
    
    # 1. AI Demand Forecasts & Smart Reorder Recommendations
    reorder_recommendations = []
    forecasts = {}
    for p in products:
        rec = get_smart_reorder_recommendation(p.id)
        if rec:
            reorder_recommendations.append(rec)
            forecasts[p.id] = get_ai_demand_forecast(p.id, forecast_days=30)

    # Filter recommendations that need reorder
    reorder_needed = [r for r in reorder_recommendations if r['needs_reorder']]

    # 2. ABC & FSN Classification Matrix
    abc_matrix = get_sku_classification()

    # 3. Inventory Health Score
    health_score = calculate_inventory_health_score()

    # 4. Supplier Intelligence Metrics
    suppliers = get_supplier_intelligence()

    locations = Location.query.filter_by(location_type='Internal').all()

    return render_template(
        'intelligence/index.html',
        reorder_recommendations=reorder_recommendations,
        reorder_needed=reorder_needed,
        forecasts=forecasts,
        abc_matrix=abc_matrix,
        health_score=health_score,
        suppliers=suppliers,
        locations=locations
    )

@intelligence_bp.route('/auto-reorder', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def auto_reorder():
    """
    AI Smart Action: Automatically generates a draft Goods Receipt for all products flagged for reorder!
    """
    destination_location_id = request.form.get('destination_location_id', type=int)
    supplier_name = request.form.get('supplier_name', 'AI Auto-Replenishment Supplier').strip()

    if not destination_location_id:
        flash('Please select a destination storage location for AI replenishment.', 'danger')
        return redirect(url_for('intelligence.index'))

    products = Product.query.filter_by(is_active=True).all()
    reorder_lines = []

    for p in products:
        rec = get_smart_reorder_recommendation(p.id)
        if rec and rec['needs_reorder'] and rec['suggested_reorder_qty'] > 0:
            reorder_lines.append({
                'product_id': p.id,
                'qty': rec['suggested_reorder_qty']
            })

    if not reorder_lines:
        flash('No products currently require AI reordering.', 'info')
        return redirect(url_for('intelligence.index'))

    reference = f"REC-AI-{uuid.uuid4().hex[:5].upper()}"
    receipt = Receipt(
        reference=reference,
        supplier_name=supplier_name,
        destination_location_id=destination_location_id,
        status='Draft',
        created_by=current_user.id
    )
    db.session.add(receipt)
    db.session.flush()

    for line in reorder_lines:
        db.session.add(ReceiptLine(receipt_id=receipt.id, product_id=line['product_id'], quantity=line['qty']))

    db.session.commit()
    flash(f'AI Auto-Replenishment Receipt "{receipt.reference}" generated with {len(reorder_lines)} items!', 'success')
    return redirect(url_for('receipts.view', id=receipt.id))
