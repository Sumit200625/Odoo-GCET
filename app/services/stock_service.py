# app/services/stock_service.py
from datetime import datetime
from app.extensions import db
from app.models.stock import StockBalance
from app.models.operation import Receipt, Delivery, Transfer, Adjustment
from app.models.ledger import StockLedger
from app.services.inventory_ledger_service import record_inventory_transaction

def get_location_stock(product_id, location_id):
    """Return current stock quantity for a product at a location."""
    balance = StockBalance.query.filter_by(product_id=product_id, location_id=location_id).first()
    return balance.quantity if balance else 0.0

def validate_receipt(receipt_id, user_id):
    """
    Validates a receipt:
    - Increases destination stock
    - Logs immutable stock ledger entries with transaction_id
    - Updates receipt status to 'Done'
    """
    receipt = Receipt.query.get_or_404(receipt_id)
    if receipt.status == 'Done':
        raise ValueError("Receipt is already validated.")
    if receipt.status == 'Canceled':
        raise ValueError("Cannot validate a canceled receipt.")
    if not receipt.lines:
        raise ValueError("Receipt must contain at least one line item.")

    try:
        for line in receipt.lines:
            if line.quantity <= 0:
                raise ValueError(f"Invalid quantity {line.quantity} for product '{line.product.name}'. Quantity must be positive.")

            record_inventory_transaction(
                product_id=line.product_id,
                quantity_change=line.quantity,
                operation_type='Purchase receipt',
                reference=receipt.reference,
                created_by=user_id,
                destination_location_id=receipt.destination_location_id,
                batch_number=getattr(line, 'batch_number', 'BATCH-2026-001'),
                reason=f"Received from supplier '{receipt.supplier_name}'"
            )

        receipt.status = 'Done'
        receipt.validated_at = datetime.utcnow()
        db.session.commit()
        return receipt
    except Exception as e:
        db.session.rollback()
        raise e


def validate_delivery(delivery_id, user_id):
    """
    Validates a delivery order:
    - Checks stock availability at source location
    - Decreases source stock
    - Logs immutable stock ledger entries
    - Updates delivery status to 'Done'
    """
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.status == 'Done':
        raise ValueError("Delivery order is already validated.")
    if delivery.status == 'Canceled':
        raise ValueError("Cannot validate a canceled delivery order.")
    if not delivery.lines:
        raise ValueError("Delivery order must contain at least one line item.")

    try:
        # Availability Check
        for line in delivery.lines:
            if line.quantity <= 0:
                raise ValueError(f"Invalid quantity {line.quantity} for product '{line.product.name}'.")

            available = get_location_stock(line.product_id, delivery.source_location_id)
            if available < line.quantity:
                raise ValueError(
                    f"Insufficient stock for '{line.product.name}' at {delivery.source_location.full_name}. "
                    f"Available: {available} {line.product.unit}, Required: {line.quantity} {line.product.unit}."
                )

        # Deduct stock and log ledger
        for line in delivery.lines:
            record_inventory_transaction(
                product_id=line.product_id,
                quantity_change=-line.quantity,
                operation_type='Sale dispatch',
                reference=delivery.reference,
                created_by=user_id,
                source_location_id=delivery.source_location_id,
                batch_number=getattr(line, 'batch_allocated', 'BATCH-2026-001'),
                reason=f"Delivered to customer '{delivery.customer_name}'"
            )

        delivery.status = 'Done'
        delivery.validated_at = datetime.utcnow()
        db.session.commit()
        return delivery
    except Exception as e:
        db.session.rollback()
        raise e


def validate_transfer(transfer_id, user_id):
    """
    Validates internal transfer:
    - Checks source stock availability
    - Decreases source location stock & increases destination stock
    - Logs immutable stock ledger entries
    - Updates transfer status to 'Done'
    """
    transfer = Transfer.query.get_or_404(transfer_id)
    if transfer.status == 'Done':
        raise ValueError("Transfer is already validated.")
    if transfer.status == 'Canceled':
        raise ValueError("Cannot validate a canceled transfer.")
    if transfer.source_location_id == transfer.destination_location_id:
        raise ValueError("Source location and destination location must be different.")
    if not transfer.lines:
        raise ValueError("Transfer must contain at least one line item.")

    try:
        for line in transfer.lines:
            if line.quantity <= 0:
                raise ValueError(f"Invalid quantity {line.quantity} for product '{line.product.name}'.")

            available = get_location_stock(line.product_id, transfer.source_location_id)
            if available < line.quantity:
                raise ValueError(
                    f"Insufficient stock for '{line.product.name}' at {transfer.source_location.full_name}. "
                    f"Available: {available} {line.product.unit}, Requested: {line.quantity} {line.product.unit}."
                )

        for line in transfer.lines:
            # Outflow from source
            record_inventory_transaction(
                product_id=line.product_id,
                quantity_change=-line.quantity,
                operation_type='Stock transfer',
                reference=transfer.reference,
                created_by=user_id,
                source_location_id=transfer.source_location_id,
                destination_location_id=transfer.destination_location_id,
                batch_number=getattr(line, 'batch_number', 'BATCH-2026-001'),
                reason=f"Transferred to {transfer.destination_location.full_name}"
            )

            # Inflow to destination
            record_inventory_transaction(
                product_id=line.product_id,
                quantity_change=line.quantity,
                operation_type='Stock transfer',
                reference=transfer.reference,
                created_by=user_id,
                source_location_id=transfer.source_location_id,
                destination_location_id=transfer.destination_location_id,
                batch_number=getattr(line, 'batch_number', 'BATCH-2026-001'),
                reason=f"Transferred from {transfer.source_location.full_name}"
            )

        transfer.status = 'Done'
        transfer.validated_at = datetime.utcnow()
        db.session.commit()
        return transfer
    except Exception as e:
        db.session.rollback()
        raise e


def validate_adjustment(adjustment_id, user_id):
    """
    Validates physical stock adjustment:
    - Sets stock balance to physical counted quantity
    - Calculates exact difference (counted - recorded)
    - Logs ledger entry recording the difference
    - Updates adjustment status to 'Done'
    """
    adjustment = Adjustment.query.get_or_404(adjustment_id)
    if adjustment.status == 'Done':
        raise ValueError("Adjustment is already validated.")
    if adjustment.status == 'Canceled':
        raise ValueError("Cannot validate a canceled adjustment.")
    if not adjustment.lines:
        raise ValueError("Adjustment must contain at least one line item.")

    try:
        for line in adjustment.lines:
            if line.counted_quantity < 0:
                raise ValueError(f"Counted quantity cannot be negative for '{line.product.name}'.")

            balance = StockBalance.query.filter_by(
                product_id=line.product_id,
                location_id=adjustment.location_id
            ).first()

            recorded_qty = balance.quantity if balance else 0.0
            difference = line.counted_quantity - recorded_qty
            
            line.recorded_quantity = recorded_qty
            line.difference = difference

            record_inventory_transaction(
                product_id=line.product_id,
                quantity_change=difference,
                operation_type='Adjustment',
                reference=adjustment.reference,
                created_by=user_id,
                source_location_id=adjustment.location_id,
                reason=adjustment.reason or "Inventory Physical Count Adjustment"
            )

        adjustment.status = 'Done'
        adjustment.validated_at = datetime.utcnow()
        db.session.commit()
        return adjustment
    except Exception as e:
        db.session.rollback()
        raise e
