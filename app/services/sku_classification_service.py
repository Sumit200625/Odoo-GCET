# app/services/sku_classification_service.py
"""
SKU Classification Engine for StockSense.
Computes multi-dimensional classifications:
1. ABC Classification (Annual Consumption Value: A=70%, B=20%, C=10%)
2. XYZ Classification (Demand Variability CV: X=Stable <=0.25, Y=Variable <=0.75, Z=Erratic >0.75)
3. 9-Box Matrix (AX, AY, AZ, BX, BY, BZ, CX, CY, CZ)
4. FSN Velocity (Fast, Slow, Non-moving)
5. Policy mapping: Cycle-count frequency, Safety Stock policy, Picking Priority
"""

import numpy as np
from datetime import datetime, timedelta
from app.extensions import db
from app.models.product import Product
from app.services.forecasting_engine import get_historical_daily_sales

def compute_sku_classifications():
    """
    Scans all active products, computes ABC/XYZ and FSN matrix, updates products, and returns results.
    """
    products = Product.query.filter_by(is_active=True).all()
    if not products:
        return []

    # 1. ABC Classification by Annual Consumption Value
    product_values = []
    for p in products:
        series = get_historical_daily_sales(p.id, days=90)
        total_qty_90d = float(np.sum(series))
        annual_val = total_qty_90d * 4.0 * (p.unit_cost or 50.0)
        product_values.append({
            'product': p,
            'annual_value': annual_val,
            'series': series
        })

    # Sort descending by annual value
    sorted_by_val = sorted(product_values, key=lambda x: x['annual_value'], reverse=True)
    total_val_sum = sum(x['annual_value'] for x in sorted_by_val) or 1.0

    cum_val = 0.0
    classified = []

    for item in sorted_by_val:
        p = item['product']
        annual_val = item['annual_value']
        series = item['series']

        cum_val += annual_val
        cum_pct = (cum_val / total_val_sum) * 100.0

        # ABC Tag
        if cum_pct <= 70.0:
            abc = 'A'
        elif cum_pct <= 90.0:
            abc = 'B'
        else:
            abc = 'C'

        # XYZ Tag (Coefficient of Variation CV = std_dev / mean)
        mean_demand = float(np.mean(series))
        std_demand = float(np.std(series))
        cv = (std_demand / mean_demand) if mean_demand > 0 else 1.0

        if cv <= 0.25:
            xyz = 'X'
        elif cv <= 0.75:
            xyz = 'Y'
        else:
            xyz = 'Z'

        # FSN Velocity
        daily_avg = float(np.mean(series[-30:])) if len(series) >= 30 else mean_demand
        if daily_avg >= 2.0:
            fsn = 'F'
        elif daily_avg >= 0.2:
            fsn = 'S'
        else:
            fsn = 'N'

        # Update product model
        p.abc_class = abc
        p.xyz_class = xyz
        p.velocity_class = fsn

        # Derive Policy Recommendations
        cycle_count_freq = "Monthly" if abc == 'A' else ("Quarterly" if abc == 'B' else "Bi-Annually")
        review_freq = "Daily" if abc == 'A' or xyz == 'Z' else "Weekly"
        picking_prio = "High-Velocity Bay" if fsn == 'F' else "Standard Storage"

        classified.append({
            'product_id': p.id,
            'sku': p.sku,
            'name': p.name,
            'abc_class': abc,
            'xyz_class': xyz,
            'matrix_code': f"{abc}{xyz}",
            'velocity_class': fsn,
            'annual_value': round(annual_val, 2),
            'cv_score': round(cv, 2),
            'daily_avg_demand': round(daily_avg, 2),
            'cycle_count_frequency': cycle_count_freq,
            'review_frequency': review_freq,
            'recommended_picking_location': picking_prio
        })

    db.session.commit()
    return classified
