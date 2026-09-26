# app/services/inventory_health_service.py
"""
Explainable Inventory Health Score Engine for StockSense.
Calculates score from 0 to 100 with clear deduction breakdowns.
Categories: Healthy, Monitor, At Risk, Critical, Dead Stock.
"""

from app.extensions import db
from app.models.product import Product
from app.models.warehouse import Warehouse, Location
from app.models.stock import StockBalance
from app.models.supplier import Supplier
from app.models.ai_intelligence import InventoryHealthScore
from app.services.forecasting_engine import generate_ai_forecast_for_sku

def calculate_sku_health_score(product_id):
    """Calculates health score for a specific SKU with itemized deduction explanations."""
    product = Product.query.get_or_404(product_id)
    fc = generate_ai_forecast_for_sku(product_id)
    
    score = 100.0
    deductions = []

    # 1. Stockout Risk Deduction
    total_stock = product.total_stock
    daily_rate = fc['daily_rate']
    lead_time = product.lead_time_days or 5
    days_rem = total_stock / max(0.1, daily_rate)

    if total_stock <= 0:
        score -= 30.0
        deductions.append("Out of stock (-30 pts)")
    elif days_rem <= lead_time:
        score -= 20.0
        deductions.append(f"Stockout risk within lead time (-20 pts)")
    elif total_stock <= product.reorder_level:
        score -= 10.0
        deductions.append("Below reorder point (-10 pts)")

    # 2. Overstock / Dead Stock Deduction
    if days_rem >= 120.0:
        score -= 25.0
        deductions.append("Severe overstock / dead stock (>120 days) (-25 pts)")
    elif days_rem >= 90.0:
        score -= 15.0
        deductions.append("Overstock condition (>90 days) (-15 pts)")

    # 3. Expiry Risk Deduction
    expired_cnt = sum(1 for b in product.stock_balances if b.is_expired)
    near_exp_cnt = sum(1 for b in product.stock_balances if 0 <= b.days_until_expiry <= 30 and not b.is_expired)

    if expired_cnt > 0:
        score -= 25.0
        deductions.append("Contains expired stock batches (-25 pts)")
    elif near_exp_cnt > 0:
        score -= 15.0
        deductions.append("Stock expiring within 30 days (-15 pts)")

    # 4. Forecast Accuracy Deduction
    acc = fc['accuracy_pct']
    if acc < 75.0:
        score -= 15.0
        deductions.append(f"Low forecast confidence ({acc}%) (-15 pts)")

    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 85.0:
        category = 'Healthy'
    elif score >= 70.0:
        category = 'Monitor'
    elif score >= 50.0:
        category = 'At Risk'
    elif score >= 30.0:
        category = 'Critical'
    else:
        category = 'Dead Stock'

    explanation = f"Health Score: {score}. " + (", ".join(deductions) if deductions else "All inventory metrics optimal.")

    return {
        'product_id': product.id,
        'sku': product.sku,
        'name': product.name,
        'health_score': score,
        'category': category,
        'deductions': deductions,
        'explanation': explanation
    }

def calculate_system_wide_health_score():
    """Calculates aggregate system-wide warehouse inventory health score."""
    products = Product.query.filter_by(is_active=True).all()
    if not products:
        return {'overall_score': 100.0, 'category': 'Healthy', 'explanation': 'No active inventory items.'}

    scores = [calculate_sku_health_score(p.id)['health_score'] for p in products]
    overall = round(sum(scores) / len(scores), 1)

    if overall >= 85.0:
        category = 'Healthy'
    elif overall >= 70.0:
        category = 'Monitor'
    elif overall >= 50.0:
        category = 'At Risk'
    else:
        category = 'Critical'

    # Save to DB
    hs = InventoryHealthScore(
        entity_type='System',
        overall_score=overall,
        category=category,
        explanation_text=f"System Health Score: {overall} across {len(products)} active SKUs."
    )
    db.session.add(hs)
    db.session.commit()

    return {
        'overall_score': overall,
        'category': category,
        'sku_count': len(products),
        'explanation': f"System-wide Inventory Health Index: {overall}% ({category})."
    }
