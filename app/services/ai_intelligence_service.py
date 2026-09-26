# app/services/ai_intelligence_service.py
import math
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.product import Product
from app.models.stock import StockBalance
from app.models.ledger import StockLedger
from app.models.warehouse import Location

def calculate_product_velocity(product_id, days=30):
    """
    Calculates daily consumption/outflow rate for a product based on stock ledger history.
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Query negative quantity changes (deliveries, transfer out, negative adjustments)
    total_outflow = db.session.query(func.coalesce(func.sum(func.abs(StockLedger.quantity_change)), 0.0)).filter(
        StockLedger.product_id == product_id,
        StockLedger.created_at >= since_date,
        StockLedger.quantity_change < 0
    ).scalar()

    daily_velocity = round(total_outflow / max(1, days), 2)
    return daily_velocity

def get_ai_demand_forecast(product_id, forecast_days=30):
    """
    AI Demand Forecasting: Predicts future demand using moving average velocity & trend coefficient.
    """
    v7 = calculate_product_velocity(product_id, days=7)
    v30 = calculate_product_velocity(product_id, days=30)
    
    # Weighted velocity (higher weight to recent 7-day velocity)
    weighted_daily_rate = (v7 * 0.6) + (v30 * 0.4)
    if weighted_daily_rate == 0:
        weighted_daily_rate = 1.2 # Baseline minimal demand assumption

    forecasted_demand = round(weighted_daily_rate * forecast_days, 1)
    return {
        'daily_burn_rate': round(weighted_daily_rate, 2),
        'forecast_30d': forecasted_demand,
        'trend': 'Increasing' if v7 > v30 else ('Stable' if v7 == v30 else 'Decreasing')
    }

def calculate_dynamic_safety_stock(product_id):
    """
    Dynamic Safety Stock calculation considering lead time and demand variability.
    Formula: Z (1.65 for 95% service level) * Lead Time Factor * Daily Velocity
    """
    product = Product.query.get(product_id)
    if not product:
        return 10.0

    forecast = get_ai_demand_forecast(product_id, forecast_days=30)
    daily_rate = forecast['daily_burn_rate']
    lead_time = product.lead_time_days or 5

    # Safety Stock = 1.65 * sqrt(Lead Time) * Daily Rate
    safety_stock = round(1.65 * math.sqrt(lead_time) * daily_rate, 1)
    return max(float(product.reorder_level or 10.0), safety_stock)

def get_smart_reorder_recommendation(product_id):
    """
    Smart Reorder Recommendation: Calculates suggested reorder quantity & urgency.
    """
    product = Product.query.get(product_id)
    if not product:
        return None

    forecast = get_ai_demand_forecast(product_id, forecast_days=30)
    daily_rate = forecast['daily_burn_rate']
    total_stock = product.total_stock
    lead_time = product.lead_time_days or 5
    safety_stock = calculate_dynamic_safety_stock(product_id)

    # Days of Inventory Remaining (DIR)
    days_remaining = round(total_stock / daily_rate, 1) if daily_rate > 0 else 999.0

    # Reorder Point (ROP) = (Daily Demand * Lead Time) + Safety Stock
    reorder_point = round((daily_rate * lead_time) + safety_stock, 1)

    needs_reorder = total_stock <= reorder_point
    suggested_qty = max(0.0, round((forecast['forecast_30d'] + safety_stock) - total_stock, 1))

    # Risk Classification
    if total_stock <= 0:
        risk_level = 'CRITICAL' # Out of stock
        risk_color = '#ef4444'
    elif days_remaining <= lead_time:
        risk_level = 'HIGH'     # Will run out before replenishment arrives
        risk_color = '#f59e0b'
    elif total_stock > (reorder_point * 3):
        risk_level = 'OVERSTOCK' # Excess capital tied up
        risk_color = '#3b82f6'
    else:
        risk_level = 'HEALTHY'
        risk_color = '#10b981'

    return {
        'product': product,
        'total_stock': total_stock,
        'daily_burn_rate': daily_rate,
        'days_remaining': days_remaining,
        'reorder_point': reorder_point,
        'safety_stock': safety_stock,
        'needs_reorder': needs_reorder,
        'suggested_reorder_qty': suggested_qty if needs_reorder else 0.0,
        'risk_level': risk_level,
        'risk_color': risk_color
    }

def get_sku_classification():
    """
    ABC & FSN Classification of Products.
    - ABC: Based on Inventory Value (A = Top 70% value, B = Next 20%, C = Bottom 10%)
    - FSN: Fast, Slow, Non-moving based on transaction frequency
    """
    products = Product.query.filter_by(is_active=True).all()
    if not products:
        return []

    # Sort products by total inventory value descending
    sorted_by_value = sorted(products, key=lambda p: p.total_value, reverse=True)
    total_value_sum = sum(p.total_value for p in sorted_by_value) or 1.0

    cumulative = 0.0
    classified = []
    for p in sorted_by_value:
        cumulative += p.total_value
        pct = (cumulative / total_value_sum) * 100.0

        if pct <= 70.0:
            abc = 'A'
        elif pct <= 90.0:
            abc = 'B'
        else:
            abc = 'C'

        v30 = calculate_product_velocity(p.id, days=30)
        if v30 > 2.0:
            fsn = 'F' # Fast moving
        elif v30 > 0.2:
            fsn = 'S' # Slow moving
        else:
            fsn = 'N' # Non-moving

        p.abc_class = abc
        p.fsn_class = fsn

        classified.append({
            'product': p,
            'abc_class': abc,
            'fsn_class': fsn,
            'daily_velocity': v30,
            'total_value': p.total_value
        })

    db.session.commit()
    return classified

def calculate_inventory_health_score():
    """
    Calculates aggregate Warehouse Inventory Health Score (0 to 100%).
    Based on:
    - % of Healthy Stock items (40%)
    - Space Utilization Efficiency (30%)
    - Zero Out-of-Stock Ratio (30%)
    """
    products = Product.query.filter_by(is_active=True).all()
    if not products:
        return 100.0

    healthy_count = 0
    in_stock_count = 0

    for p in products:
        rec = get_smart_reorder_recommendation(p.id)
        if rec['risk_level'] == 'HEALTHY':
            healthy_count += 1
        if p.total_stock > 0:
            in_stock_count += 1

    healthy_ratio = healthy_count / len(products)
    in_stock_ratio = in_stock_count / len(products)

    # Calculate average location space utilization
    locations = Location.query.all()
    optimum_capacity_count = sum(1 for l in locations if 10.0 <= l.occupancy_percentage <= 85.0)
    space_efficiency = optimum_capacity_count / max(1, len(locations))

    health_score = round((healthy_ratio * 40.0) + (space_efficiency * 30.0) + (in_stock_ratio * 30.0), 1)
    return min(100.0, max(0.0, health_score))
