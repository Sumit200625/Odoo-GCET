# app/services/warehouse_intelligence_service.py
from datetime import datetime, timedelta
from app.models.warehouse import Location, Warehouse
from app.models.stock import StockBalance
from app.models.operation import Delivery, Receipt
from app.models.supplier import Supplier

def get_warehouse_space_utilization():
    """
    Space Utilization Analytics across warehouses & storage locations.
    """
    locations = Location.query.all()
    matrix = []

    for loc in locations:
        occ_pct = loc.occupancy_percentage
        if occ_pct >= 90.0:
            status = 'OVERFILLED'
            color = '#ef4444'
        elif occ_pct >= 75.0:
            status = 'NEAR CAPACITY'
            color = '#f59e0b'
        elif occ_pct <= 10.0:
            status = 'UNDERUTILIZED'
            color = '#3b82f6'
        else:
            status = 'OPTIMAL'
            color = '#10b981'

        matrix.append({
            'location': loc,
            'warehouse': loc.warehouse,
            'occupied_qty': loc.occupied_quantity,
            'max_capacity': loc.max_capacity or 500.0,
            'available_capacity': loc.available_capacity,
            'occupancy_pct': occ_pct,
            'status': status,
            'color': color
        })

    return matrix

def recommend_smart_putaway(product_id, quantity):
    """
    Smart Put-Away Assistant: Recommends optimal location to store incoming product based on:
    1. Highest available capacity
    2. Internal location type
    """
    locations = Location.query.filter_by(location_type='Internal').all()
    recommendations = []

    for loc in locations:
        avail = loc.available_capacity
        if avail >= quantity:
            score = 100 - loc.occupancy_percentage
            recommendations.append({
                'location': loc,
                'available_capacity': avail,
                'occupancy_pct': loc.occupancy_percentage,
                'score': score,
                'reason': f"Sufficient capacity ({avail} units free in {loc.zone})"
            })

    # Sort by score descending
    sorted_recs = sorted(recommendations, key=lambda x: x['score'], reverse=True)
    return sorted_recs

def get_expiry_and_aging_analysis(days_threshold=60):
    """
    Expiry & Aging Analysis: Identifies stock batches nearing expiry.
    """
    cutoff = datetime.utcnow() + timedelta(days=days_threshold)
    balances = StockBalance.query.filter(
        StockBalance.quantity > 0
    ).all()

    expiry_alerts = []
    for b in balances:
        if b.expiry_date:
            days_left = b.days_until_expiry
            if days_left <= 0:
                urgency = 'EXPIRED'
                color = '#ef4444'
            elif days_left <= 15:
                urgency = 'CRITICAL (<= 15 Days)'
                color = '#dc2626'
            elif days_left <= 30:
                urgency = 'WARNING (<= 30 Days)'
                color = '#f59e0b'
            elif days_left <= days_threshold:
                urgency = 'MONITOR'
                color = '#3b82f6'
            else:
                continue

            expiry_alerts.append({
                'balance': b,
                'product': b.product,
                'location': b.location,
                'batch_number': b.batch_number,
                'expiry_date': b.expiry_date,
                'days_left': days_left,
                'urgency': urgency,
                'color': color
            })

    # Sort by days left ascending (FEFO priority)
    return sorted(expiry_alerts, key=lambda x: x['days_left'])

def recommend_fefo_picking(product_id, location_id, requested_qty):
    """
    FEFO (First Expired First Out) Picking Recommendation for outbound deliveries.
    """
    balances = StockBalance.query.filter_by(
        product_id=product_id,
        location_id=location_id
    ).filter(StockBalance.quantity > 0).all()

    # Sort by expiry_date ascending (or received_date if no expiry)
    sorted_batches = sorted(
        balances,
        key=lambda b: (b.expiry_date if b.expiry_date else datetime.max, b.received_date)
    )

    picks = []
    remaining = requested_qty
    for b in sorted_batches:
        if remaining <= 0:
            break
        pick_qty = min(b.quantity, remaining)
        remaining -= pick_qty
        picks.append({
            'balance': b,
            'batch_number': b.batch_number,
            'pick_qty': pick_qty,
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d') if b.expiry_date else 'N/A'
        })

    return {
        'picks': picks,
        'fulfilled': remaining <= 0,
        'shortfall': max(0.0, remaining)
    }

def get_outbound_picking_priorities():
    """
    Outbound Order Picking Priority Ranking.
    Ranks pending delivery orders by creation date & stock readiness.
    """
    deliveries = Delivery.query.filter(Delivery.status.in_(['Draft', 'Ready'])).order_by(Delivery.created_at.asc()).all()
    prioritized = []

    for idx, d in enumerate(deliveries):
        priority = 'HIGH' if idx == 0 or d.status == 'Ready' else 'NORMAL'
        prioritized.append({
            'delivery': d,
            'priority': priority,
            'status': d.status,
            'queue_position': idx + 1
        })

    return prioritized

def get_supplier_intelligence():
    """
    Supplier Intelligence Performance Metrics.
    """
    suppliers = Supplier.query.all()
    return suppliers
