# app/services/stock_service.py
from datetime import datetime
from app.extensions import db
from app.models.stock import StockBalance
from app.models.operation import Receipt, Delivery, Transfer, Adjustment
from app.models.ledger import StockLedger

def get_location_stock(product_id, location_id):
    """Return the current stock quantity for a product at a location."""
    balance = StockBalance.query.filter_by(product_id=product_id, location_id=location_id).first()
    return balance.quantity if balance else 0.0

def validate_receipt(receipt_id, user_id):
    """
    Validate a receipt:
    - Increases destination stock
    - Creates stock ledger entries
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
            
            balance = StockBalance.query.filter_by(
                product_id=line.product_id,
                location_id=receipt.destination_location_id
            ).first()

            if not balance:
                balance = StockBalance(
                    product_id=line.product_id,
                    location_id=receipt.destination_location_id,
                    quantity=0.0
                )
                db.session.add(balance)

            qty_before = balance.quantity
            qty_after = qty_before + line.quantity
            balance.quantity = qty_after

            ledger_entry = StockLedger(
                product_id=line.product_id,
                location_id=receipt.destination_location_id,
                operation_type='Receipt',
                reference=receipt.reference,
                quantity_change=line.quantity,
                quantity_before=qty_before,
                quantity_after=qty_after,
                reason=f"Received from {receipt.supplier_name}",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(ledger_entry)

        receipt.status = 'Done'
        receipt.validated_at = datetime.utcnow()
        db.session.commit()
        return receipt
    except Exception as e:
        db.session.rollback()
        raise e


def validate_delivery(delivery_id, user_id):
    """
    Validate a delivery:
    - Checks stock availability at source location
    - Decreases source stock
    - Creates stock ledger entries
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
        # Pass 1: Availability check
        for line in delivery.lines:
            if line.quantity <= 0:
                raise ValueError(f"Invalid quantity {line.quantity} for product '{line.product.name}'. Quantity must be positive.")

            available = get_location_stock(line.product_id, delivery.source_location_id)
            if available < line.quantity:
                raise ValueError(
                    f"Insufficient stock for '{line.product.name}' at {delivery.source_location.full_name}. "
                    f"Available: {available} {line.product.unit}, Required: {line.quantity} {line.product.unit}."
                )

        # Pass 2: Deduct stock and log ledger
        for line in delivery.lines:
            balance = StockBalance.query.filter_by(
                product_id=line.product_id,
                location_id=delivery.source_location_id
            ).first()

            qty_before = balance.quantity
            qty_after = qty_before - line.quantity
            balance.quantity = qty_after

            ledger_entry = StockLedger(
                product_id=line.product_id,
                location_id=delivery.source_location_id,
                operation_type='Delivery',
                reference=delivery.reference,
                quantity_change=-line.quantity,
                quantity_before=qty_before,
                quantity_after=qty_after,
                reason=f"Delivered to {delivery.customer_name}",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(ledger_entry)

        delivery.status = 'Done'
        delivery.validated_at = datetime.utcnow()
        db.session.commit()
        return delivery
    except Exception as e:
        db.session.rollback()
        raise e


def validate_transfer(transfer_id, user_id):
    """
    Validate internal transfer:
    - Checks source stock availability
    - Decreases source location stock
    - Increases destination location stock
    - Keeps total stock balance unchanged
    - Creates two ledger entries (outflow from source, inflow to destination)
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
        # Pass 1: Availability Check
        for line in transfer.lines:
            if line.quantity <= 0:
                raise ValueError(f"Invalid quantity {line.quantity} for product '{line.product.name}'. Quantity must be positive.")

            available = get_location_stock(line.product_id, transfer.source_location_id)
            if available < line.quantity:
                raise ValueError(
                    f"Insufficient stock for '{line.product.name}' at {transfer.source_location.full_name}. "
                    f"Available: {available} {line.product.unit}, Requested: {line.quantity} {line.product.unit}."
                )

        # Pass 2: Transfer Stock
        for line in transfer.lines:
            # Source deduction
            src_balance = StockBalance.query.filter_by(
                product_id=line.product_id,
                location_id=transfer.source_location_id
            ).first()

            src_before = src_balance.quantity
            src_after = src_before - line.quantity
            src_balance.quantity = src_after

            ledger_src = StockLedger(
                product_id=line.product_id,
                location_id=transfer.source_location_id,
                operation_type='Transfer Out',
                reference=transfer.reference,
                quantity_change=-line.quantity,
                quantity_before=src_before,
                quantity_after=src_after,
                reason=f"Transferred to {transfer.destination_location.full_name}",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(ledger_src)

            # Destination addition
            dst_balance = StockBalance.query.filter_by(
                product_id=line.product_id,
                location_id=transfer.destination_location_id
            ).first()

            if not dst_balance:
                dst_balance = StockBalance(
                    product_id=line.product_id,
                    location_id=transfer.destination_location_id,
                    quantity=0.0
                )
                db.session.add(dst_balance)

            dst_before = dst_balance.quantity
            dst_after = dst_before + line.quantity
            dst_balance.quantity = dst_after

            ledger_dst = StockLedger(
                product_id=line.product_id,
                location_id=transfer.destination_location_id,
                operation_type='Transfer In',
                reference=transfer.reference,
                quantity_change=line.quantity,
                quantity_before=dst_before,
                quantity_after=dst_after,
                reason=f"Transferred from {transfer.source_location.full_name}",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(ledger_dst)

        transfer.status = 'Done'
        transfer.validated_at = datetime.utcnow()
        db.session.commit()
        return transfer
    except Exception as e:
        db.session.rollback()
        raise e


def validate_adjustment(adjustment_id, user_id):
    """
    Validate stock adjustment:
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

            if not balance:
                balance = StockBalance(
                    product_id=line.product_id,
                    location_id=adjustment.location_id,
                    quantity=0.0
                )
                db.session.add(balance)

            recorded_qty = balance.quantity
            difference = line.counted_quantity - recorded_qty
            
            line.recorded_quantity = recorded_qty
            line.difference = difference
            balance.quantity = line.counted_quantity

            ledger_entry = StockLedger(
                product_id=line.product_id,
                location_id=adjustment.location_id,
                operation_type='Adjustment',
                reference=adjustment.reference,
                quantity_change=difference,
                quantity_before=recorded_qty,
                quantity_after=line.counted_quantity,
                reason=adjustment.reason or "Inventory Audit Adjustment",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(ledger_entry)

        adjustment.status = 'Done'
        adjustment.validated_at = datetime.utcnow()
        db.session.commit()
        return adjustment
    except Exception as e:
        db.session.rollback()
        raise e
