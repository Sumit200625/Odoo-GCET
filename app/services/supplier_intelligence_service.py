# app/services/supplier_intelligence_service.py
"""
Supplier Intelligence & Scorecard Service for StockSense.
- Calculates 0-100 Supplier Performance Scorecards
- Supplier Classifications: Strategic, Reliable, Monitor, High Risk, Blocked
- Multi-Objective Supplier Ranking for Purchase Orders
"""

from app.extensions import db
from app.models.supplier import Supplier
from app.models.operation import PurchaseOrder

def evaluate_all_suppliers():
    """
    Recalculates performance metrics and classifications for all suppliers.
    """
    suppliers = Supplier.query.all()
    results = []

    for s in suppliers:
        score = s.computed_score
        classification = s.computed_classification
        
        s.supplier_score = score
        s.classification = classification

        # PO History Stats
        po_count = PurchaseOrder.query.filter_by(supplier_id=s.id).count()

        results.append({
            'supplier_id': s.id,
            'name': s.name,
            'code': s.code,
            'lead_time_days': s.lead_time_days,
            'lead_time_variance': s.lead_time_variance_days,
            'on_time_rate': s.on_time_delivery_rate,
            'fill_rate_pct': s.fill_rate_pct,
            'quality_rate': s.quality_acceptance_rate,
            'defect_rate_pct': s.defect_rate_pct,
            'response_time_hrs': s.response_time_hours,
            'po_count': po_count,
            'supplier_score': score,
            'classification': classification
        })

    db.session.commit()
    return results

def rank_suppliers_for_po(product, objective='Balanced'):
    """
    Ranks suppliers based on user objective: Lowest Cost, Fastest Delivery, Highest Reliability, Best Quality, Balanced.
    """
    suppliers = Supplier.query.filter_by(is_active=True).all()
    rankings = []

    for s in suppliers:
        cost = product.unit_cost or 50.0
        lead = s.lead_time_days or 5
        rel = s.computed_score
        qual = s.quality_acceptance_rate or 95.0

        if objective == 'Lowest Cost':
            obj_score = 100.0 - cost
        elif objective == 'Fastest Delivery':
            obj_score = 100.0 - (lead * 10.0)
        elif objective == 'Highest Reliability':
            obj_score = rel
        elif objective == 'Best Quality':
            obj_score = qual
        else: # Balanced
            obj_score = (rel * 0.35) + (qual * 0.35) + ((10.0 - min(10, lead)) * 3.0)

        rankings.append({
            'supplier': s,
            'objective_score': round(obj_score, 1),
            'lead_time_days': lead,
            'reliability_score': rel,
            'unit_cost': cost,
            'moq': s.minimum_order_quantity or 10.0,
            'classification': s.computed_classification
        })

    return sorted(rankings, key=lambda x: x['objective_score'], reverse=True)
