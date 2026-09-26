# app/services/grocery_intelligence_service.py
"""
Grocery Retail Intelligence Service for StockSense.
- Store Inventory Management (Shelf vs Backroom vs Warehouse)
- POS Sales Transaction Recording & Auto Shelf Replenishment Task Generation
- Expiry, Freshness & Waste Breakdown
- Retail Pulse Cards & Store Health Matrix
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.product import Product
from app.models.grocery import Store, ShelfLocation, POSSale, POSSaleItem, ReplenishmentTask, WasteRecord
from app.models.stock import StockBalance
from app.services.inventory_ledger_service import record_inventory_transaction

def get_grocery_dashboard_data(store_id=1):
    """
    Compiles real-time metrics for Grocery Retail Intelligence Dashboard.
    """
    products = Product.query.filter_by(is_active=True).all()
    store = Store.query.get(store_id) or Store.query.first()

    total_store_value = sum((p.shelf_stock + p.backroom_stock) * (p.unit_cost or 50.0) for p in products)
    
    # Calculate shelf availability percentage
    full_shelves = sum(1 for p in products if p.shelf_stock >= (p.shelf_capacity * 0.4))
    shelf_availability_pct = round((full_shelves / max(1, len(products))) * 100.0, 1)

    # Today's POS Sales
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_sales_val = db.session.query(func.coalesce(func.sum(POSSale.total_amount), 0.0)).filter(
        POSSale.created_at >= today_start
    ).scalar()

    # Total Waste Cost
    total_waste_val = db.session.query(func.coalesce(func.sum(WasteRecord.total_cost_waste), 0.0)).scalar()

    # Expiry & Fresh-Product Risk
    cutoff_15d = datetime.utcnow() + timedelta(days=15)
    near_expiry_skus = Product.query.filter(
        Product.is_expiry_sensitive == True,
        Product.is_active == True
    ).all()

    # Pending Replenishment Tasks
    pending_replenishments = ReplenishmentTask.query.filter_by(status='Pending').all()

    # Retail Pulse Cards
    fastest_moving = sorted(products, key=lambda p: p.shelf_stock, reverse=True)[0] if products else None
    highest_waste_item = Product.query.filter(Product.is_perishable == True).first()

    return {
        'store': store,
        'today_sales_val': round(today_sales_val, 2),
        'total_inventory_value': round(total_store_value, 2),
        'shelf_availability_pct': shelf_availability_pct,
        'total_waste_val': round(total_waste_val, 2),
        'pending_replenishments': pending_replenishments,
        'near_expiry_count': len(near_expiry_skus),
        'products': products,
        'retail_pulse': {
            'fastest_moving': fastest_moving,
            'highest_waste_item': highest_waste_item
        }
    }

def record_pos_checkout_sale(store_id, line_items, user_id, payment_method='UPI / Card'):
    """
    Records Point-of-Sale checkout:
    1. Deducts quantity from SKU's `shelf_stock`.
    2. Creates POSSale and POSSaleItem records.
    3. Logs immutable StockLedger entry (`Sale dispatch`).
    4. Automatically generates a Backroom-to-Shelf ReplenishmentTask if shelf stock falls below 5 units!
    """
    store = Store.query.get_or_404(store_id)
    receipt_num = f"POS-{uuid.uuid4().hex[:8].upper()}"
    
    total_amt = 0.0
    sale = POSSale(
        receipt_number=receipt_num,
        store_id=store.id,
        total_amount=0.0,
        total_items_count=len(line_items),
        payment_method=payment_method,
        created_by=user_id
    )
    db.session.add(sale)
    db.session.flush()

    # Find primary store location for ledger logging
    store_loc = StockBalance.query.first()
    loc_id = store_loc.location_id if store_loc else 1

    for item in line_items:
        prod_id = item['product_id']
        qty = float(item['quantity'])
        product = Product.query.get_or_404(prod_id)
        
        unit_price = product.active_price
        line_total = round(qty * unit_price, 2)
        total_amt += line_total

        sale_item = POSSaleItem(
            pos_sale_id=sale.id,
            product_id=prod_id,
            quantity=qty,
            unit_price=unit_price,
            total_price=line_total,
            batch_number=item.get('batch_number', 'POS-BATCH')
        )
        db.session.add(sale_item)

        # Deduct Shelf Stock
        product.shelf_stock = max(0.0, product.shelf_stock - qty)

        # Record Ledger Transaction
        record_inventory_transaction(
            product_id=prod_id,
            quantity_change=-qty,
            operation_type='Sale dispatch',
            reference=receipt_num,
            created_by=user_id,
            source_location_id=loc_id,
            reason=f"POS Sale Checkout Receipt {receipt_num}"
        )

        # Auto-trigger Backroom-to-Shelf Replenishment if shelf stock is low
        if product.shelf_stock <= 5.0 and product.backroom_stock > 0:
            task_code = f"REP-{uuid.uuid4().hex[:8].upper()}"
            repl_qty = min(product.backroom_stock, round(product.shelf_capacity - product.shelf_stock, 1))
            
            task = ReplenishmentTask(
                task_code=task_code,
                store_id=store.id,
                product_id=prod_id,
                quantity=repl_qty,
                source_area="Backroom",
                destination_shelf=f"Aisle {product.category_id} Shelf 1",
                priority="HIGH",
                status="Pending"
            )
            db.session.add(task)

    sale.total_amount = round(total_amt, 2)
    db.session.commit()
    return sale

def record_waste_disposal(product_id, quantity, reason, user_id, store_id=1, batch_number=None):
    """Records product waste/spoilage and deducts stock."""
    product = Product.query.get_or_404(product_id)
    cost = product.unit_cost or 50.0
    total_waste_cost = round(quantity * cost, 2)

    code = f"WST-{uuid.uuid4().hex[:8].upper()}"
    waste = WasteRecord(
        record_code=code,
        product_id=product_id,
        store_id=store_id,
        batch_number=batch_number or 'BATCH-WASTE',
        quantity=quantity,
        unit_cost=cost,
        total_cost_waste=total_waste_cost,
        reason=reason,
        action_taken=f"Scrapped due to {reason}. Disposed.",
        recorded_by=user_id
    )
    db.session.add(waste)

    # Deduct stock
    if product.shelf_stock >= quantity:
        product.shelf_stock -= quantity
    else:
        product.backroom_stock = max(0.0, product.backroom_stock - quantity)

    # Ledger record
    store_loc = StockBalance.query.first()
    loc_id = store_loc.location_id if store_loc else 1

    record_inventory_transaction(
        product_id=product_id,
        quantity_change=-quantity,
        operation_type='Expiry' if 'Expired' in reason else 'Damage',
        reference=code,
        created_by=user_id,
        source_location_id=loc_id,
        reason=f"Waste Record: {reason}"
    )

    db.session.commit()
    return waste
