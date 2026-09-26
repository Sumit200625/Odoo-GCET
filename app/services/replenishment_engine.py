# app/services/replenishment_engine.py
"""
Explainable Replenishment Engine for StockSense.
Calculates:
- Dynamic Safety Stock (Z-score based on service level targets & variability)
- Reorder Point (ROP = (Demand * Lead Time) + Safety Stock)
- Economic Order Quantity (EOQ = sqrt((2 * Demand * Ordering Cost) / Holding Cost))
- Minimum Order Quantity (MOQ) and Pack Size rounding
- Multi-Objective Supplier Selection (Lowest Cost, Fastest Delivery, Highest Reliability)
- Human Approval Workflow: Generated -> Reviewed -> Approved -> Executed -> Received -> Closed
"""

import math
import uuid
import json
from datetime import datetime, timedelta
from app.extensions import db
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.supplier import Supplier
from app.models.stock import StockBalance
from app.models.operation import PurchaseOrder, PurchaseOrderItem
from app.models.ai_intelligence import ReorderRecommendation, SafetyStockPolicy, AuditLog
from app.services.forecasting_engine import generate_ai_forecast_for_sku

def calculate_dynamic_safety_stock(product_id, target_service_level_pct=95.0):
    """
    Dynamic Safety Stock calculation:
    Formula: Z * sqrt(Lead Time * StdDev_Demand^2 + Daily_Demand^2 * StdDev_LeadTime^2)
    """
    product = Product.query.get_or_404(product_id)
    fc = generate_ai_forecast_for_sku(product_id)
    daily_rate = fc['daily_rate']
    lead_time = product.lead_time_days or 5

    # Z-factor mapping based on service level
    z_map = {99.0: 2.33, 98.0: 2.05, 95.0: 1.65, 90.0: 1.28, 85.0: 1.04}
    z_score = z_map.get(target_service_level_pct, 1.65)

    # Class-based adjustments
    if product.abc_class == 'A' or product.is_critical:
        z_score += 0.2
    if product.xyz_class == 'Z': # High demand variability
        z_score += 0.3

    std_dev_demand = max(0.5, daily_rate * 0.3)
    std_dev_lead_time = 1.0

    safety_stock = z_score * math.sqrt(
        (lead_time * (std_dev_demand ** 2)) + ((daily_rate ** 2) * (std_dev_lead_time ** 2))
    )

    return round(max(float(product.reorder_level or 5.0), safety_stock), 1)

def calculate_economic_order_quantity(product, annual_demand):
    """
    EOQ Formula: sqrt((2 * D * S) / H)
    D = Annual Demand, S = Fixed Ordering Cost ($100 default), H = Holding Cost ($/unit/year)
    """
    ordering_cost = 100.0
    holding_cost = (product.unit_cost or 50.0) * ((product.holding_cost_annual_pct or 20.0) / 100.0)
    holding_cost = max(1.0, holding_cost)

    eoq = math.sqrt((2 * max(1.0, annual_demand) * ordering_cost) / holding_cost)
    return round(max(product.minimum_order_quantity or 10.0, eoq), 1)

def select_best_supplier_for_reorder(product, objective='Balanced'):
    """
    Multi-Objective Supplier Selection comparing cost, lead time, and reliability.
    """
    suppliers = Supplier.query.filter_by(is_active=True).all()
    if not suppliers:
        return None

    best_sup = None
    best_score = -1.0

    for s in suppliers:
        price = product.unit_cost or 50.0
        lead = s.lead_time_days or 5
        rel = s.computed_score

        if objective == 'Lowest Cost':
            score = 100.0 - price
        elif objective == 'Fastest Delivery':
            score = 100.0 - lead * 10.0
        elif objective == 'Highest Reliability':
            score = rel
        else: # Balanced
            score = (rel * 0.5) + ((10.0 - min(10, lead)) * 3.0) + (50.0 * 0.2)

        if score > best_score:
            best_score = score
            best_sup = s

    return best_sup

def generate_reorder_recommendation_for_sku(product_id, warehouse_id=1):
    """
    Generates an explainable Reorder Recommendation for a SKU.
    """
    product = Product.query.get_or_404(product_id)
    warehouse = Warehouse.query.get(warehouse_id) or Warehouse.query.first()
    fc = generate_ai_forecast_for_sku(product_id)
    
    daily_rate = fc['daily_rate']
    forecast_30d = fc['forecast_30d']
    total_stock = product.total_stock
    
    # Calculate stock parameters
    safety_stock = calculate_dynamic_safety_stock(product_id)
    lead_time = product.lead_time_days or 5
    reorder_point = round((daily_rate * lead_time) + safety_stock, 1)

    # Determine recommended quantity
    net_requirement = max(0.0, (forecast_30d + safety_stock) - total_stock)
    moq = product.minimum_order_quantity or 10.0
    pack_size = product.pack_size or 1
    
    eoq = calculate_economic_order_quantity(product, annual_demand=daily_rate * 365.0)
    raw_qty = max(net_requirement, eoq, moq)
    
    # Pack size rounding
    recommended_qty = math.ceil(raw_qty / pack_size) * pack_size

    # Supplier selection
    supplier = select_best_supplier_for_reorder(product, objective='Balanced')
    
    # Action determination
    if total_stock <= reorder_point:
        action = 'Reorder'
        urgency = 'CRITICAL' if total_stock <= 0 else ('HIGH' if total_stock <= (reorder_point * 0.5) else 'MEDIUM')
        problem = f"Current inventory ({total_stock} {product.unit}) is below the calculated Reorder Point ({reorder_point} {product.unit}). Stockout predicted in {round(total_stock/max(0.1, daily_rate), 1)} days."
        benefit = f"Prevents revenue loss of ~${round(daily_rate * (product.selling_price or 75.0) * 14, 2)} and maintains {product.abc_class} SKU service level target."
    elif total_stock > (reorder_point * 3.5):
        action = 'Discount Slow-Moving'
        urgency = 'MEDIUM'
        recommended_qty = 0.0
        problem = f"Inventory level ({total_stock} {product.unit}) exceeds 3.5x safety threshold. Excess capital tied up."
        benefit = "Frees up warehouse storage capacity and reduces annual holding costs."
    else:
        return None # No action required

    rec_code = f"REC-{uuid.uuid4().hex[:8].upper()}"
    rec = ReorderRecommendation(
        rec_code=rec_code,
        product_id=product.id,
        warehouse_id=warehouse.id,
        supplier_id=supplier.id if supplier else None,
        current_stock=total_stock,
        reserved_stock=0.0,
        in_transit_stock=0.0,
        forecasted_demand_30d=forecast_30d,
        safety_stock=safety_stock,
        reorder_point=reorder_point,
        recommended_action=action,
        recommended_quantity=recommended_qty,
        expected_delivery_date=datetime.utcnow() + timedelta(days=lead_time),
        expected_stockout_date=datetime.utcnow() + timedelta(days=int(total_stock/max(0.1, daily_rate))),
        estimated_coverage_days=round((total_stock + recommended_qty) / max(0.1, daily_rate), 1),
        problem_detected=problem,
        data_used_json=json.dumps({
            "forecast_30d": forecast_30d,
            "daily_burn_rate": daily_rate,
            "lead_time_days": lead_time,
            "eoq": eoq,
            "moq": moq,
            "accuracy_pct": fc['accuracy_pct']
        }),
        predicted_impact=f"Restores stock buffer to {round(recommended_qty + total_stock, 1)} units and covers demand for ~{round((total_stock + recommended_qty)/max(0.1, daily_rate), 1)} days.",
        expected_benefit=benefit,
        urgency_level=urgency,
        confidence_level_pct=fc['confidence_pct'],
        financial_impact=round(recommended_qty * (product.unit_cost or 50.0), 2),
        approval_status='Generated'
    )

    db.session.add(rec)
    db.session.commit()
    return rec

def approve_reorder_recommendation(rec_id, user_id):
    """
    Approves recommendation and automatically converts it into a formal Purchase Order.
    """
    rec = ReorderRecommendation.query.get_or_404(rec_id)
    if rec.approval_status in ['Approved', 'Executed']:
        raise ValueError("Recommendation has already been approved or executed.")

    rec.approval_status = 'Approved'
    rec.approved_by_id = user_id

    # Create Purchase Order
    po_num = f"PO-{uuid.uuid4().hex[:8].upper()}"
    po = PurchaseOrder(
        po_number=po_num,
        supplier_id=rec.supplier_id or 1,
        warehouse_id=rec.warehouse_id,
        status='Approved',
        total_amount=rec.financial_impact,
        expected_delivery_date=rec.expected_delivery_date,
        created_by=user_id,
        approved_by=user_id,
        notes=f"Auto-generated PO from Approved Reorder Recommendation {rec.rec_code}"
    )
    db.session.add(po)
    db.session.flush()

    po_item = PurchaseOrderItem(
        po_id=po.id,
        product_id=rec.product_id,
        ordered_quantity=rec.recommended_quantity,
        unit_cost=rec.product.unit_cost or 50.0
    )
    db.session.add(po_item)

    rec.approval_status = 'Executed'
    rec.generated_po_id = po.id

    audit = AuditLog(
        action_type="Approve_Reorder",
        entity_name="ReorderRecommendation",
        entity_id=rec.rec_code,
        description=f"Approved reorder of {rec.recommended_quantity} {rec.product.unit} for {rec.product.name}. Generated Purchase Order {po_num}.",
        previous_state="Generated",
        new_state="Executed",
        performed_by=user_id
    )
    db.session.add(audit)

    db.session.commit()
    return po
