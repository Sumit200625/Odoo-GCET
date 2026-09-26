# app/services/picking_outbound_engine.py
"""
Outbound Management & Pick Path Optimization Engine for StockSense.
- FEFO (First Expired First Out) & FIFO Batch Allocation Engine
- Pick Task Generation & Pick Path Sequence Optimization (Aisle/Rack/Shelf/Bin routing)
- Short-Pick Handling & Substitute Item Recommendations
- Packing & Dispatch Verification
"""

import uuid
from datetime import datetime
from app.extensions import db
from app.models.product import Product
from app.models.stock import StockBalance, InventoryBatch
from app.models.warehouse import Location
from app.models.operation import Delivery, DeliveryLine, PickTask, SalesOrder
from app.services.inventory_ledger_service import record_inventory_transaction

def allocate_batches_fefo_or_fifo(product_id, location_id, requested_qty):
    """
    FEFO (First Expired First Out) / FIFO Allocation Engine.
    Filters out expired, quarantined, and damaged stock.
    Sorts candidate batches by earliest expiry date (FEFO) or earliest received date (FIFO).
    """
    batches = InventoryBatch.query.filter_by(
        product_id=product_id,
        location_id=location_id,
        quality_status='Passed'
    ).filter(InventoryBatch.current_quantity > 0).all()

    # Exclude expired batches
    valid_batches = [b for b in batches if not b.is_expired]

    # Sort: Expiring earliest first (FEFO), then oldest received date (FIFO)
    sorted_batches = sorted(
        valid_batches,
        key=lambda b: (b.expiry_date if b.expiry_date else datetime.max, b.received_date)
    )

    allocations = []
    remaining = requested_qty

    for b in sorted_batches:
        if remaining <= 0:
            break
        alloc_qty = min(b.current_quantity, remaining)
        remaining -= alloc_qty
        allocations.append({
            'batch_id': b.id,
            'batch_number': b.batch_number,
            'allocated_quantity': alloc_qty,
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d') if b.expiry_date else 'N/A',
            'days_left': b.days_until_expiry
        })

    is_fulfilled = remaining <= 0
    shortfall = max(0.0, remaining)

    return {
        'allocations': allocations,
        'is_fulfilled': is_fulfilled,
        'shortfall': shortfall,
        'allocated_total': requested_qty - shortfall
    }

def generate_optimized_pick_tasks_for_delivery(delivery_id, picking_method='Single', user_id=1):
    """
    Generates pick tasks for a delivery order and sorts them into an optimal pick path sequence.
    Pick path ordering: Sorted by Location Zone -> Aisle -> Rack -> Shelf -> Bin.
    """
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.status == 'Done':
        raise ValueError("Delivery order is already validated.")

    pick_tasks = []

    for line in delivery.lines:
        alloc_res = allocate_batches_fefo_or_fifo(line.product_id, delivery.source_location_id, line.quantity)
        
        for alloc in alloc_res['allocations']:
            task_code = f"PCK-{uuid.uuid4().hex[:8].upper()}"
            
            task = PickTask(
                task_code=task_code,
                delivery_id=delivery.id,
                product_id=line.product_id,
                batch_number=alloc['batch_number'],
                source_location_id=delivery.source_location_id,
                requested_quantity=alloc['allocated_quantity'],
                picked_quantity=0.0,
                status='Pending',
                assigned_operator_id=user_id
            )
            db.session.add(task)
            pick_tasks.append(task)

    # Sort tasks into optimal warehouse pick path sequence
    sorted_tasks = sorted(
        pick_tasks,
        key=lambda t: (
            t.source_location.zone if t.source_location else '',
            t.source_location.aisle if t.source_location else '',
            t.source_location.rack if t.source_location else '',
            t.source_location.shelf if t.source_location else '',
            t.source_location.bin_code if t.source_location else ''
        )
    )

    for idx, t in enumerate(sorted_tasks):
        t.pick_path_sequence = idx + 1

    delivery.status = 'Picking'
    delivery.picking_method = picking_method
    db.session.commit()

    return sorted_tasks

def confirm_pick_task_execution(task_id, picked_qty, operator_user_id, short_pick_reason=None):
    """
    Confirms operator pick scan. Handles short-picks, updates stock, and logs ledger entry.
    """
    task = PickTask.query.get_or_404(task_id)
    if task.status == 'Completed':
        raise ValueError("Pick task is already completed.")

    task.picked_quantity = picked_qty
    task.completed_at = datetime.utcnow()

    if picked_qty < task.requested_quantity:
        task.status = 'Short_Picked'
        task.short_pick_reason = short_pick_reason or "Insufficient physical stock found at bin location."
    else:
        task.status = 'Completed'

    # Deduct stock from source location
    record_inventory_transaction(
        product_id=task.product_id,
        quantity_change=-picked_qty,
        operation_type='Picking',
        reference=task.task_code,
        created_by=operator_user_id,
        source_location_id=task.source_location_id,
        batch_number=task.batch_number,
        reason=f"Picked for Delivery Order {task.delivery.reference if task.delivery else 'Outbound'}"
    )

    db.session.commit()

    # Substitute Recommendation if short-picked
    substitute_info = None
    if task.status == 'Short_Picked':
        product = Product.query.get(task.product_id)
        same_cat_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True
        ).all()
        substitutes = [p for p in same_cat_products if p.total_stock >= (task.requested_quantity - picked_qty)]
        if substitutes:
            substitute_info = {
                'recommended_substitute_sku': substitutes[0].sku,
                'recommended_substitute_name': substitutes[0].name,
                'available_stock': substitutes[0].total_stock
            }

    return {
        'task': task,
        'substitute_info': substitute_info
    }
