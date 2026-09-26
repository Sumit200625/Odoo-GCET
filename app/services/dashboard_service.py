# app/services/dashboard_service.py
from sqlalchemy import func
from app.extensions import db
from app.models.product import Product
from app.models.stock import StockBalance
from app.models.operation import Receipt, Delivery, Transfer
from app.models.ledger import StockLedger

def get_dashboard_kpis(warehouse_id=None):
    """
    Computes real-time KPI metrics for the StockSense dashboard.
    """
    total_products = Product.query.filter_by(is_active=True).count()

    # Total stock quantity query
    total_qty_query = db.session.query(func.coalesce(func.sum(StockBalance.quantity), 0.0))
    if warehouse_id:
        total_qty_query = total_qty_query.join(StockBalance.location).filter(StockBalance.location.has(warehouse_id=warehouse_id))
    total_stock_quantity = total_qty_query.scalar()

    # Product low stock / out of stock calculations
    products = Product.query.filter_by(is_active=True).all()
    low_stock_count = 0
    out_of_stock_count = 0

    for product in products:
        stock = product.total_stock
        if stock <= 0:
            out_of_stock_count += 1
        elif stock <= product.reorder_level:
            low_stock_count += 1

    pending_receipts = Receipt.query.filter(Receipt.status.in_(['Draft', 'Waiting'])).count()
    pending_deliveries = Delivery.query.filter(Delivery.status.in_(['Draft', 'Ready'])).count()
    internal_transfers_scheduled = Transfer.query.filter(Transfer.status.in_(['Draft', 'Waiting'])).count()

    return {
        'total_products': total_products,
        'total_stock_quantity': round(total_stock_quantity, 2),
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'pending_receipts': pending_receipts,
        'pending_deliveries': pending_deliveries,
        'internal_transfers_scheduled': internal_transfers_scheduled
    }

def get_recent_movements(limit=8):
    return StockLedger.query.order_by(StockLedger.created_at.desc()).limit(limit).all()

def get_low_stock_alerts():
    products = Product.query.filter_by(is_active=True).all()
    alerts = []
    for product in products:
        stock = product.total_stock
        if stock <= product.reorder_level:
            alerts.append({
                'product': product,
                'total_stock': stock,
                'reorder_level': product.reorder_level,
                'status': 'Out of Stock' if stock <= 0 else 'Low Stock'
            })
    return alerts
