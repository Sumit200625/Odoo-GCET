# app/routes/pricing.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.grocery import PriceHistory
from app.services.price_intelligence_service import update_product_price, recommend_near_expiry_markdown

pricing_bp = Blueprint('pricing', __name__, url_prefix='/pricing')

@pricing_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    products = Product.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            prod_id = int(request.form.get('product_id'))
            new_p = float(request.form.get('new_price'))
            p_type = request.form.get('price_type', 'Standard')
            rationale = request.form.get('rationale', 'Manager Manual Price Adjustment')
            
            update_product_price(prod_id, new_p, p_type, rationale, current_user.id)
            flash("Price change saved successfully! Immutable PriceHistory record logged.", "success")
        except Exception as e:
            flash(f"Price update failed: {str(e)}", "danger")
        return redirect(url_for('pricing.index'))

    # Near-expiry markdown recommendations
    markdown_recs = []
    for p in products:
        m_rec = recommend_near_expiry_markdown(p.id)
        if m_rec:
            markdown_recs.append(m_rec)

    histories = PriceHistory.query.order_by(PriceHistory.created_at.desc()).limit(20).all()

    return render_template(
        'pricing/index.html',
        products=products,
        markdown_recs=markdown_recs,
        histories=histories
    )
