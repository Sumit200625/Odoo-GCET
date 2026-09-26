# app/services/ledger_service.py
from app.models.ledger import StockLedger
from app.models.product import Product

def get_filtered_ledger(product_id=None, location_id=None, operation_type=None, search=None, limit=100):
    query = StockLedger.query.order_by(StockLedger.created_at.desc())

    if product_id:
        query = query.filter(StockLedger.product_id == int(product_id))

    if location_id:
        query = query.filter(StockLedger.location_id == int(location_id))

    if operation_type:
        if operation_type == 'Transfer':
            query = query.filter(StockLedger.operation_type.in_(['Transfer Out', 'Transfer In', 'Transfer']))
        else:
            query = query.filter(StockLedger.operation_type == operation_type)

    if search:
        search_pattern = f"%{search}%"
        query = query.join(Product).filter(
            (StockLedger.reference.ilike(search_pattern)) |
            (Product.name.ilike(search_pattern)) |
            (Product.sku.ilike(search_pattern))
        )

    return query.limit(limit).all()
