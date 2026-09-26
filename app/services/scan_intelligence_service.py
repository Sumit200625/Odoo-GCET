# app/services/scan_intelligence_service.py
"""
Scan-to-Intelligence Engine for StockSense.
- Supports EAN-13, UPC, Code 128, QR, GS1, PLU codes
- Modes: 1. Product Lookup, 2. Transaction, 3. Intelligence
- Builds complete 5-Section Product Intelligence Panel
- Quick Action Handlers (Sale, Reorder, Transfer, Putaway, Pick, Replenish, Damage, Expiry, Markdown, Simulation)
"""

from app.extensions import db
from app.models.product import Product
from app.services.inventory_health_service import calculate_sku_health_score
from app.services.forecasting_engine import generate_ai_forecast_for_sku
from app.services.replenishment_engine import generate_reorder_recommendation_for_sku, calculate_dynamic_safety_stock, select_best_supplier_for_reorder

def process_scanned_barcode(barcode_or_sku, scan_mode='Intelligence', store_id=1):
    """
    Parses scanned barcode or SKU input and builds the full 5-Section Product Intelligence Panel.
    """
    query = barcode_or_sku.strip()
    product = Product.query.filter(
        (Product.barcode == query) | (Product.sku == query) | (Product.plu_code == query)
    ).first()

    if not product:
        # Fallback search by partial name
        product = Product.query.filter(Product.name.ilike(f"%{query}%")).first()

    if not product:
        return {
            'found': False,
            'query': query,
            'error_message': f"Product with barcode/SKU '{query}' not found in StockSense index."
        }

    # Gather AI & Inventory Intelligence
    health = calculate_sku_health_score(product.id)
    fc = generate_ai_forecast_for_sku(product.id)
    safety_stock = calculate_dynamic_safety_stock(product.id)
    best_supplier = select_best_supplier_for_reorder(product)
    
    reorder_rec = generate_reorder_recommendation_for_sku(product.id)
    rec_action = reorder_rec.urgency_level if reorder_rec else 'STABLE'

    # Earliest expiry date
    earliest_expiry = "N/A"
    days_left = 999
    for b in product.stock_balances:
        if b.days_until_expiry < days_left:
            days_left = b.days_until_expiry
            if b.expiry_date:
                earliest_expiry = b.expiry_date.strftime('%Y-%m-%d')

    # Construct 5-Section Intelligence Panel
    panel = {
        'found': True,
        'scan_mode': scan_mode,
        'identity': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode or 'N/A',
            'plu_code': product.plu_code or 'N/A',
            'brand': product.brand or 'Generic',
            'category': product.category.name if product.category else 'General',
            'unit': product.unit
        },
        'commercial': {
            'unit_cost': product.unit_cost,
            'mrp': product.mrp,
            'active_price': product.active_price,
            'discount_pct': product.discount_pct,
            'margin_pct': product.margin_pct,
            'promotion': 'Active Festival Deal' if product.promotion_price else ('Markdown Clearance' if product.markdown_price else 'Standard Price')
        },
        'inventory_position': {
            'total_stock': product.total_stock,
            'shelf_stock': product.shelf_stock,
            'backroom_stock': product.backroom_stock,
            'warehouse_stock': product.warehouse_stock,
            'earliest_expiry': earliest_expiry,
            'days_until_expiry': days_left,
            'picking_priority': 'FEFO Priority' if product.is_expiry_sensitive else 'FIFO Priority'
        },
        'ai_intelligence': {
            'health_score': health['health_score'],
            'health_category': health['category'],
            'daily_burn_rate': fc['daily_rate'],
            'forecast_30d': fc['forecast_30d'],
            'safety_stock': safety_stock,
            'risk_level': rec_action,
            'suggested_supplier': best_supplier.name if best_supplier else 'Default Vendor',
            'predicted_price': round(product.active_price * 0.95, 2) if product.is_expiry_sensitive else product.active_price,
            'recommended_action': f"Reorder {fc['forecast_30d']} units" if rec_action in ['CRITICAL', 'HIGH'] else "Maintain active stock buffer"
        },
        'quick_actions': [
            {'action': 'add_to_sale', 'label': 'Add to POS Sale', 'icon': 'fa-cart-plus'},
            {'action': 'replenish_shelf', 'label': 'Replenish Shelf', 'icon': 'fa-boxes-packing'},
            {'action': 'create_reorder', 'label': 'Create Reorder', 'icon': 'fa-rotate-right'},
            {'action': 'record_markdown', 'label': 'Apply Markdown', 'icon': 'fa-tags'},
            {'action': 'record_waste', 'label': 'Log Expiry / Waste', 'icon': 'fa-trash-can'},
            {'action': 'open_simulation', 'label': 'What-If Simulation', 'icon': 'fa-flask-vial'}
        ]
    }

    return panel
