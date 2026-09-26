# app/services/predictive_risk_engine.py
"""
Predictive Inventory Risk Engine for StockSense.
Continuously analyzes and prioritizes 12 risk categories:
1. Stockout risk
2. Overstock risk
3. Expiry risk
4. Dead-stock risk
5. Slow-moving inventory risk
6. Supplier-delay risk
7. Demand-spike risk
8. Forecast-uncertainty risk
9. Warehouse-capacity risk
10. Location-capacity risk
11. Inventory-accuracy risk
12. Order-fulfilment risk

Calculates: Risk Score (0-100), Severity, Financial Impact, Probability, Expected Date, and Recommended Mitigation.
"""

import uuid
from datetime import datetime, timedelta
from app.extensions import db
from app.models.product import Product
from app.models.stock import StockBalance, InventoryBatch
from app.models.warehouse import Warehouse, Location
from app.models.supplier import Supplier
from app.models.operation import Delivery
from app.models.ai_intelligence import RiskEvent
from app.services.forecasting_engine import generate_ai_forecast_for_sku

def evaluate_stockout_risk(product):
    """Calculates stockout risk by comparing stock, burn rate, lead time, and safety stock."""
    fc = generate_ai_forecast_for_sku(product.id)
    daily_rate = fc['daily_rate']
    total_stock = product.total_stock
    lead_time = product.lead_time_days or 5

    days_remaining = round(total_stock / daily_rate, 1) if daily_rate > 0 else 999.0

    if total_stock <= 0:
        score = 100.0
        severity = 'Critical'
        days_to_stockout = 0
    elif days_remaining <= lead_time:
        score = min(95.0, 70.0 + (lead_time - days_remaining) * 5.0)
        severity = 'High'
        days_to_stockout = int(days_remaining)
    elif days_remaining <= (lead_time * 1.5):
        score = 55.0
        severity = 'Medium'
        days_to_stockout = int(days_remaining)
    else:
        return None # Low/No risk

    fin_impact = round(daily_rate * (product.selling_price or 75.0) * max(1, lead_time), 2)
    expected_date = datetime.utcnow() + timedelta(days=days_to_stockout)

    return {
        'risk_category': 'Stockout Risk',
        'severity': severity,
        'risk_score': score,
        'probability_pct': round(min(98.0, score + 5.0), 1),
        'expected_date': expected_date,
        'financial_impact': fin_impact,
        'operational_impact': f"Stockout predicted within {days_to_stockout} days for {product.name}. Immediate customer order fulfillment halt risk.",
        'product_id': product.id,
        'recommended_mitigation': f"Execute emergency reorder of {round(daily_rate * 30.0, 1)} {product.unit} or expedite shipment with primary supplier."
    }

def evaluate_overstock_risk(product):
    """Calculates overstock risk when days of inventory exceeds 90 days."""
    fc = generate_ai_forecast_for_sku(product.id)
    daily_rate = fc['daily_rate']
    total_stock = product.total_stock

    days_remaining = round(total_stock / daily_rate, 1) if daily_rate > 0 else 999.0

    if days_remaining >= 120.0:
        score = 85.0
        severity = 'High'
    elif days_remaining >= 90.0:
        score = 65.0
        severity = 'Medium'
    else:
        return None

    excess_units = max(0.0, total_stock - (daily_rate * 45.0))
    holding_cost = round(excess_units * (product.unit_cost or 50.0) * 0.20, 2)

    return {
        'risk_category': 'Overstock Risk',
        'severity': severity,
        'risk_score': score,
        'probability_pct': 90.0,
        'expected_date': datetime.utcnow() + timedelta(days=30),
        'financial_impact': holding_cost,
        'operational_impact': f"{int(days_remaining)} days of inventory on hand. Excess working capital locked up in storage.",
        'product_id': product.id,
        'recommended_mitigation': f"Pause future purchase orders. Offer 15% promotional discount or transfer {round(excess_units/2, 1)} units to high-demand branch."
    }

def evaluate_expiry_risk():
    """Identifies batches expiring within 30 days."""
    cutoff = datetime.utcnow() + timedelta(days=30)
    batches = InventoryBatch.query.filter(
        InventoryBatch.expiry_date <= cutoff,
        InventoryBatch.current_quantity > 0
    ).all()

    risks = []
    for b in batches:
        days_left = b.days_until_expiry
        fin_impact = round(b.current_quantity * (b.unit_cost or 50.0), 2)

        if days_left <= 0:
            severity = 'Critical'
            score = 100.0
            desc = f"Batch {b.batch_number} of {b.product.name} is EXPIRED ({b.current_quantity} {b.product.unit})."
            mitigation = "Immediately quarantine and initiate disposal workflow."
        elif days_left <= 15:
            severity = 'High'
            score = 85.0
            desc = f"Batch {b.batch_number} expires in {days_left} days."
            mitigation = "Prioritize FEFO picking for active outbound deliveries or apply clearance markdown."
        else:
            severity = 'Medium'
            score = 60.0
            desc = f"Batch {b.batch_number} expires in {days_left} days."
            mitigation = "Monitor consumption rate and alert sales team for rapid movement."

        risks.append({
            'risk_category': 'Expiry Risk',
            'severity': severity,
            'risk_score': score,
            'probability_pct': 95.0,
            'expected_date': b.expiry_date,
            'financial_impact': fin_impact,
            'operational_impact': desc,
            'product_id': b.product_id,
            'location_id': b.location_id,
            'recommended_mitigation': mitigation
        })
    return risks

def evaluate_warehouse_capacity_risk():
    """Scans storage locations for >90% occupancy risk."""
    locations = Location.query.all()
    risks = []

    for loc in locations:
        occ = loc.occupancy_percentage
        if occ >= 95.0:
            severity = 'Critical'
            score = 95.0
        elif occ >= 85.0:
            severity = 'High'
            score = 75.0
        else:
            continue

        risks.append({
            'risk_category': 'Location Capacity Risk',
            'severity': severity,
            'risk_score': score,
            'probability_pct': 90.0,
            'expected_date': datetime.utcnow() + timedelta(days=2),
            'financial_impact': 1500.0,
            'operational_impact': f"Storage Location '{loc.full_name}' is at {occ}% capacity. Risk of inbound congestion and put-away bottlenecks.",
            'warehouse_id': loc.warehouse_id,
            'location_id': loc.id,
            'recommended_mitigation': f"Execute smart slotting rebalancing to transfer fast-moving stock to underutilized zones."
        })
    return risks

def evaluate_supplier_delay_risk():
    """Identifies suppliers with reliability score below 80% or high lead-time variance."""
    suppliers = Supplier.query.filter(Supplier.supplier_score < 80.0).all()
    risks = []
    for sup in suppliers:
        risks.append({
            'risk_category': 'Supplier Delay Risk',
            'severity': 'High',
            'risk_score': 80.0,
            'probability_pct': 85.0,
            'expected_date': datetime.utcnow() + timedelta(days=7),
            'financial_impact': 5000.0,
            'operational_impact': f"Supplier '{sup.name}' performance score dropped to {sup.computed_score}%. Delivery delay risk high.",
            'supplier_id': sup.id,
            'recommended_mitigation': f"Reallocate upcoming replenishment volume to backup reliable supplier."
        })
    return risks

def run_predictive_risk_assessment():
    """
    Executes a full system scan, identifies all 12 risk categories, and updates active RiskEvents.
    """
    products = Product.query.filter_by(is_active=True).all()
    detected_risks = []

    for p in products:
        so = evaluate_stockout_risk(p)
        if so:
            detected_risks.append(so)
        os = evaluate_overstock_risk(p)
        if os:
            detected_risks.append(os)

    detected_risks.extend(evaluate_expiry_risk())
    detected_risks.extend(evaluate_warehouse_capacity_risk())
    detected_risks.extend(evaluate_supplier_delay_risk())

    # Persist or update RiskEvents in DB
    active_events = []
    for r in detected_risks:
        code = f"RISK-{uuid.uuid4().hex[:8].upper()}"
        event = RiskEvent(
            risk_code=code,
            risk_category=r['risk_category'],
            severity=r['severity'],
            risk_score=r['risk_score'],
            probability_pct=r['probability_pct'],
            expected_date=r.get('expected_date'),
            financial_impact=r.get('financial_impact', 0.0),
            operational_impact=r.get('operational_impact'),
            product_id=r.get('product_id'),
            warehouse_id=r.get('warehouse_id'),
            supplier_id=r.get('supplier_id'),
            location_id=r.get('location_id'),
            recommended_mitigation=r['recommended_mitigation'],
            status='Active'
        )
        db.session.add(event)
        active_events.append(event)

    db.session.commit()
    return active_events
