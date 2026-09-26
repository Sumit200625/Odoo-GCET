# app/services/inventory_ledger_service.py
"""
Unified Inventory Intelligence & Ledger Service.
Manages stock balances, inventory batches, reservations, and maintains an
immutable Stock Ledger for all 12 transaction types:
1. Purchase receipt
2. Sale dispatch
3. Stock transfer
4. Return
5. Damage
6. Expiry
7. Adjustment
8. Cycle-count correction
9. Put-away
10. Picking
11. Replenishment
12. Reservation release
"""

import uuid
from datetime import datetime
from app.extensions import db
from app.models.stock import StockBalance, InventoryBatch, StockReservation
from app.models.ledger import StockLedger
from app.models.product import Product
from app.models.warehouse import Location
from app.models.ai_intelligence import AuditLog

def record_inventory_transaction(
    product_id,
    quantity_change,
    operation_type,
    reference,
    created_by,
    source_location_id=None,
    destination_location_id=None,
    batch_number=None,
    reason=None,
    unit_cost=None
):
    """
    Core immutable transaction ledger record creator.
    Guarantees stock balance update, batch updates, and ledger creation in a single transaction.
    """
    product = Product.query.get_or_404(product_id)
    cost = unit_cost or product.unit_cost or 50.0

    # Determine primary location for balance tracking
    if quantity_change < 0:
        primary_location_id = source_location_id or destination_location_id
    else:
        primary_location_id = destination_location_id or source_location_id

    if not primary_location_id:
        raise ValueError("At least source_location_id or destination_location_id must be provided.")

    balance = StockBalance.query.filter_by(
        product_id=product_id,
        location_id=primary_location_id
    ).first()

    if not balance:
        balance = StockBalance(
            product_id=product_id,
            location_id=primary_location_id,
            quantity=0.0
        )
        db.session.add(balance)
        db.session.flush()

    qty_before = balance.quantity
    qty_after = qty_before + quantity_change
    if qty_after < 0 and operation_type not in ['Adjustment', 'Damage', 'Cycle-count correction']:
        raise ValueError(f"Insufficient stock for SKU '{product.sku}'. Available: {qty_before}, Requested Change: {quantity_change}")

    balance.quantity = qty_after
    balance.updated_at = datetime.utcnow()

    # Track inventory batch if provided
    if batch_number:
        batch = InventoryBatch.query.filter_by(
            batch_number=batch_number,
            product_id=product_id,
            location_id=primary_location_id
        ).first()
        if batch:
            batch.current_quantity = max(0.0, batch.current_quantity + quantity_change)
        else:
            batch = InventoryBatch(
                batch_number=batch_number,
                product_id=product_id,
                location_id=primary_location_id,
                initial_quantity=max(0.0, quantity_change),
                current_quantity=max(0.0, quantity_change),
                unit_cost=cost
            )
            db.session.add(batch)

    # Create Immutable Stock Ledger Record
    txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    ledger_entry = StockLedger(
        transaction_id=txn_id,
        product_id=product_id,
        batch_number=batch_number or 'DEFAULT',
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        location_id=primary_location_id,
        operation_type=operation_type,
        reference=reference,
        quantity_change=quantity_change,
        quantity_before=qty_before,
        quantity_after=qty_after,
        unit_cost=cost,
        total_value_change=round(quantity_change * cost, 2),
        reason=reason or f"Operation: {operation_type}",
        created_by=created_by,
        created_at=datetime.utcnow()
    )
    db.session.add(ledger_entry)

    # Audit Log
    audit = AuditLog(
        action_type=f"Stock_{operation_type.replace(' ', '_')}",
        entity_name="StockBalance",
        entity_id=str(balance.id),
        description=f"Recorded {operation_type} of {quantity_change} {product.unit} for {product.name} ({product.sku}). Ref: {reference}",
        previous_state=str(qty_before),
        new_state=str(qty_after),
        performed_by=created_by
    )
    db.session.add(audit)

    db.session.commit()
    return ledger_entry

def reserve_stock_for_order(order_reference, product_id, location_id, quantity, user_id):
    """
    Reserves stock for an outbound order.
    """
    balance = StockBalance.query.filter_by(product_id=product_id, location_id=location_id).first()
    if not balance or balance.available_quantity < quantity:
        available = balance.available_quantity if balance else 0.0
        raise ValueError(f"Insufficient available stock for reservation. Available: {available}, Requested: {quantity}")

    balance.reserved_quantity += quantity

    reservation = StockReservation(
        order_reference=order_reference,
        product_id=product_id,
        location_id=location_id,
        reserved_quantity=quantity,
        status='Active'
    )
    db.session.add(reservation)

    record_inventory_transaction(
        product_id=product_id,
        quantity_change=0.0,
        operation_type='Reservation release',
        reference=order_reference,
        created_by=user_id,
        source_location_id=location_id,
        reason=f"Stock Reserved {quantity} units for Order {order_reference}"
    )

    db.session.commit()
    return reservation

def get_unified_inventory_summary(product_id=None, warehouse_id=None):
    """
    Calculates unified inventory metrics across total, available, reserved, damaged, quarantined, in-transit, expired, and value.
    """
    query = db.session.query(StockBalance)
    if product_id:
        query = query.filter(StockBalance.product_id == product_id)
    if warehouse_id:
        query = query.join(Location).filter(Location.warehouse_id == warehouse_id)

    balances = query.all()

    total_qty = sum(b.quantity for b in balances)
    reserved_qty = sum(b.reserved_quantity for b in balances)
    damaged_qty = sum(b.damaged_quantity for b in balances)
    quarantined_qty = sum(b.quarantined_quantity for b in balances)
    in_transit_qty = sum(b.in_transit_quantity for b in balances)
    available_qty = max(0.0, total_qty - reserved_qty - damaged_qty - quarantined_qty)

    expired_qty = sum(b.quantity for b in balances if b.is_expired)
    near_expiry_qty = sum(b.quantity for b in balances if 0 <= b.days_until_expiry <= 30 and not b.is_expired)

    total_val = sum(b.quantity * (b.product.unit_cost or 50.0) for b in balances)

    return {
        'total_quantity': round(total_qty, 2),
        'available_quantity': round(available_qty, 2),
        'reserved_quantity': round(reserved_qty, 2),
        'damaged_quantity': round(damaged_qty, 2),
        'quarantined_quantity': round(quarantined_qty, 2),
        'in_transit_quantity': round(in_transit_qty, 2),
        'expired_quantity': round(expired_qty, 2),
        'near_expiry_quantity': round(near_expiry_qty, 2),
        'inventory_value': round(total_val, 2)
    }
