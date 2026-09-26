# run.py
import os
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG', 'default'))

def auto_seed_if_empty():
    from app.models.user import User
    from app.models.warehouse import Warehouse, Location
    from app.models.product import Category, Product
    from app.models.supplier import Supplier
    from app.models.stock import StockBalance
    from app.models.ledger import StockLedger
    from app.models.operation import Receipt, ReceiptLine, Delivery, DeliveryLine, Transfer, TransferLine, Adjustment, AdjustmentLine
    from app.services.stock_service import validate_receipt, validate_delivery, validate_transfer, validate_adjustment

    try:
        if User.query.filter_by(email="admin@stocksense.com").first() is None:
            print("Auto-seeding StockSense database with demo data...")
            admin = User(name="System Admin", email="admin@stocksense.com", role="admin")
            admin.set_password("Admin@123")

            manager = User(name="Inventory Manager", email="manager@stocksense.com", role="manager")
            manager.set_password("Manager@123")

            staff = User(name="Warehouse Staff", email="staff@stocksense.com", role="staff")
            staff.set_password("Staff@123")

            db.session.add_all([admin, manager, staff])
            db.session.commit()

            wh_main = Warehouse(name="Main Warehouse", code="WH-MAIN", address="100 Industrial Parkway, Sector 4")
            wh_prod = Warehouse(name="Production Warehouse", code="WH-PROD", address="205 Factory Road, Hub B")
            db.session.add_all([wh_main, wh_prod])
            db.session.commit()

            loc_main_store = Location(warehouse_id=wh_main.id, name="Main Store", code="LOC-MAIN-STORE", location_type="Internal", max_capacity=200.0, zone="Zone A")
            loc_rack_a = Location(warehouse_id=wh_main.id, name="Rack A", code="LOC-RACK-A", location_type="Internal", max_capacity=150.0, zone="Zone B")
            loc_prod_floor = Location(warehouse_id=wh_prod.id, name="Production Floor", code="LOC-PROD-FLR", location_type="Internal", max_capacity=300.0, zone="Fast-Pick Zone")
            loc_dispatch = Location(warehouse_id=wh_prod.id, name="Dispatch Area", code="LOC-DISPATCH", location_type="Internal", max_capacity=100.0, zone="Dispatch Bay")
            db.session.add_all([loc_main_store, loc_rack_a, loc_prod_floor, loc_dispatch])
            db.session.commit()

            cat_raw = Category(name="Raw Material")
            cat_furniture = Category(name="Furniture")
            cat_safety = Category(name="Safety Equipment")
            db.session.add_all([cat_raw, cat_furniture, cat_safety])
            db.session.commit()

            p_steel = Product(name="Steel Rods", sku="ST-RD-001", category_id=cat_raw.id, unit="kg", unit_cost=120.0, reorder_level=30.0, lead_time_days=4, abc_class="A", fsn_class="F")
            p_chairs = Product(name="Office Chairs", sku="OF-CH-002", category_id=cat_furniture.id, unit="pcs", unit_cost=85.0, reorder_level=10.0, lead_time_days=7, abc_class="B", fsn_class="S")
            p_cement = Product(name="Cement Bags", sku="CM-BG-003", category_id=cat_raw.id, unit="bags", unit_cost=15.0, reorder_level=20.0, lead_time_days=3, abc_class="B", fsn_class="F")
            p_helmets = Product(name="Safety Helmets", sku="SF-HL-004", category_id=cat_safety.id, unit="pcs", unit_cost=25.0, reorder_level=15.0, lead_time_days=5, abc_class="C", fsn_class="N")
            db.session.add_all([p_steel, p_chairs, p_cement, p_helmets])
            db.session.commit()

            sup1 = Supplier(name="Apex Steel Industries", code="SUP-APEX", contact_email="orders@apexsteel.com", lead_time_days=4, reliability_score=98.5, on_time_rate=96.0)
            sup2 = Supplier(name="Global Safety Equipment", code="SUP-GLOBAL", contact_email="sales@globalsafety.com", lead_time_days=5, reliability_score=92.0, on_time_rate=88.5)
            sup3 = Supplier(name="BuildCraft Materials", code="SUP-BUILDCRAFT", contact_email="supply@buildcraft.com", lead_time_days=3, reliability_score=95.0, on_time_rate=94.0)
            db.session.add_all([sup1, sup2, sup3])
            db.session.commit()

            now = datetime.utcnow()
            sb_steel = StockBalance(product_id=p_steel.id, location_id=loc_main_store.id, quantity=100.0, batch_number="BATCH-ST-001", expiry_date=now + timedelta(days=120))
            sb_chairs = StockBalance(product_id=p_chairs.id, location_id=loc_main_store.id, quantity=25.0, batch_number="BATCH-CH-002", expiry_date=now + timedelta(days=365))
            sb_cement = StockBalance(product_id=p_cement.id, location_id=loc_main_store.id, quantity=12.0, batch_number="BATCH-CM-003", expiry_date=now + timedelta(days=25))
            sb_helmets = StockBalance(product_id=p_helmets.id, location_id=loc_main_store.id, quantity=0.0, batch_number="BATCH-SF-004", expiry_date=now + timedelta(days=180))
            db.session.add_all([sb_steel, sb_chairs, sb_cement, sb_helmets])

            db.session.add(StockLedger(
                product_id=p_steel.id, location_id=loc_main_store.id, operation_type='Receipt', reference='INIT-STOCK',
                quantity_change=100.0, quantity_before=0.0, quantity_after=100.0, reason='Initial Stock Setup', created_by=admin.id
            ))
            db.session.add(StockLedger(
                product_id=p_chairs.id, location_id=loc_main_store.id, operation_type='Receipt', reference='INIT-STOCK',
                quantity_change=25.0, quantity_before=0.0, quantity_after=25.0, reason='Initial Stock Setup', created_by=admin.id
            ))
            db.session.add(StockLedger(
                product_id=p_cement.id, location_id=loc_main_store.id, operation_type='Receipt', reference='INIT-STOCK',
                quantity_change=12.0, quantity_before=0.0, quantity_after=12.0, reason='Initial Stock Setup', created_by=admin.id
            ))
            db.session.commit()

            rec1 = Receipt(reference="REC-00001", supplier_name="Apex Steel Industries", destination_location_id=loc_main_store.id, status="Draft", created_by=manager.id)
            db.session.add(rec1)
            db.session.flush()
            db.session.add(ReceiptLine(receipt_id=rec1.id, product_id=p_steel.id, quantity=50.0))
            db.session.commit()
            validate_receipt(rec1.id, manager.id)

            trn1 = Transfer(reference="TRN-00001", source_location_id=loc_main_store.id, destination_location_id=loc_prod_floor.id, status="Draft", created_by=staff.id)
            db.session.add(trn1)
            db.session.flush()
            db.session.add(TransferLine(transfer_id=trn1.id, product_id=p_steel.id, quantity=40.0))
            db.session.commit()
            validate_transfer(trn1.id, staff.id)

            del1 = Delivery(reference="DEL-00001", customer_name="BuildCraft Inc.", source_location_id=loc_main_store.id, status="Draft", created_by=manager.id)
            db.session.add(del1)
            db.session.flush()
            db.session.add(DeliveryLine(delivery_id=del1.id, product_id=p_steel.id, quantity=20.0))
            db.session.commit()
            validate_delivery(del1.id, manager.id)

            adj1 = Adjustment(reference="ADJ-00001", location_id=loc_main_store.id, reason="3 kg damaged Steel Rods identified during count", status="Draft", created_by=manager.id)
            db.session.add(adj1)
            db.session.flush()
            db.session.add(AdjustmentLine(adjustment_id=adj1.id, product_id=p_steel.id, recorded_quantity=90.0, counted_quantity=87.0, difference=-3.0))
            db.session.commit()
            validate_adjustment(adj1.id, manager.id)

            rec2 = Receipt(reference="REC-00002", supplier_name="Global Safety Equipment", destination_location_id=loc_main_store.id, status="Waiting", created_by=manager.id)
            db.session.add(rec2)
            db.session.flush()
            db.session.add(ReceiptLine(receipt_id=rec2.id, product_id=p_helmets.id, quantity=100.0))

            del2 = Delivery(reference="DEL-00002", customer_name="Metro Infrastructure Ltd", source_location_id=loc_main_store.id, status="Ready", created_by=staff.id)
            db.session.add(del2)
            db.session.flush()
            db.session.add(DeliveryLine(delivery_id=del2.id, product_id=p_cement.id, quantity=10.0))

            trn2 = Transfer(reference="TRN-00002", source_location_id=loc_main_store.id, destination_location_id=loc_dispatch.id, status="Draft", created_by=staff.id)
            db.session.add(trn2)
            db.session.flush()
            db.session.add(TransferLine(transfer_id=trn2.id, product_id=p_chairs.id, quantity=5.0))

            db.session.commit()
            print("Auto-seeding completed!")
    except Exception as e:
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        auto_seed_if_empty()
    app.run(host='127.0.0.1', port=5000, debug=True)
