# app/routes/intelligence.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.ai_intelligence import ReorderRecommendation, RiskEvent, Forecast
from app.services.forecasting_engine import generate_ai_forecast_for_sku
from app.services.predictive_risk_engine import run_predictive_risk_assessment
from app.services.replenishment_engine import (
    generate_reorder_recommendation_for_sku,
    approve_reorder_recommendation
)
from app.services.sku_classification_service import compute_sku_classifications
from app.services.inventory_health_service import calculate_sku_health_score, calculate_system_wide_health_score
from app.services.audit_approval_service import reject_recommendation_with_reason

intelligence_bp = Blueprint('intelligence', __name__, url_prefix='/intelligence')

@intelligence_bp.route('/')
@login_required
def overview():
    health = calculate_system_wide_health_score()
    classified = compute_sku_classifications()
    recs = ReorderRecommendation.query.order_by(ReorderRecommendation.created_at.desc()).all()
    risks = RiskEvent.query.filter_by(status='Active').order_by(RiskEvent.risk_score.desc()).all()

    return render_template(
        'intelligence/overview.html',
        health=health,
        classified=classified,
        recs=recs,
        risks=risks
    )

@intelligence_bp.route('/forecasts')
@login_required
def forecasts():
    products = Product.query.filter_by(is_active=True).all()
    selected_sku_id = request.args.get('product_id', type=int) or (products[0].id if products else None)
    
    forecast_data = None
    if selected_sku_id:
        forecast_data = generate_ai_forecast_for_sku(selected_sku_id)

    return render_template(
        'intelligence/forecasts.html',
        products=products,
        selected_sku_id=selected_sku_id,
        forecast=forecast_data
    )

@intelligence_bp.route('/risks')
@login_required
def risks():
    active_risks = run_predictive_risk_assessment()
    return render_template('intelligence/risks.html', risks=active_risks)

@intelligence_bp.route('/replenishment')
@login_required
def replenishment():
    # Scan and auto-generate pending recommendations if needed
    products = Product.query.filter_by(is_active=True).all()
    for p in products:
        try:
            generate_reorder_recommendation_for_sku(p.id)
        except Exception:
            pass

    recs = ReorderRecommendation.query.order_by(ReorderRecommendation.created_at.desc()).all()
    return render_template('intelligence/replenishment.html', recs=recs)

@intelligence_bp.route('/recommendations/<int:rec_id>/approve', methods=['POST'])
@login_required
def approve_recommendation(rec_id):
    try:
        po = approve_reorder_recommendation(rec_id, current_user.id)
        flash(f"Recommendation approved! Generated Purchase Order {po.po_number}.", "success")
    except Exception as e:
        flash(f"Approval failed: {str(e)}", "danger")
    return redirect(url_for('intelligence.replenishment'))

@intelligence_bp.route('/recommendations/<int:rec_id>/reject', methods=['POST'])
@login_required
def reject_recommendation(rec_id):
    reason = request.form.get('reason', 'Rejected by manager decision')
    try:
        reject_recommendation_with_reason(rec_id, current_user.id, reason)
        flash("Recommendation rejected. Feedback saved for model learning.", "info")
    except Exception as e:
        flash(f"Action failed: {str(e)}", "danger")
    return redirect(url_for('intelligence.replenishment'))
