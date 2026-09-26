# database/seed.py
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.stock import StockBalance
from app.models.operation import Receipt, ReceiptLine, Delivery, DeliveryLine, Transfer, TransferLine, Adjustment, AdjustmentLine
from app.models.ledger import StockLedger
from app.services.stock_service import validate_receipt, validate_delivery, validate_transfer, validate_adjustment

app = create_app('default')

def seed_database():
    with app.app_context():
        print("Resetting database tables...")
        db.drop_all()
        db.create_all()

        print("Seeding Users...")
        admin = User(name="System Admin", email="admin@stocksense.com", role="admin")
        admin.set_password("Admin@123")

        manager = User(name="Inventory Manager", email="manager@stocksense.com", role="manager")
        manager.set_password("Manager@123")

        staff = User(name="Warehouse Staff", email="staff@stocksense.com", role="staff")
        staff.set_password("Staff@123")

        db.session.add_all([admin, manager, staff])
        db.session.commit()

        print("Seeding Warehouses & Locations...")
        wh_main = Warehouse(name="Main Warehouse", code="WH-MAIN", address="100 Industrial Parkway, Sector 4")
        wh_prod = Warehouse(name="Production Warehouse", code="WH-PROD", address="205 Factory Road, Hub B")

        db.session.add_all([wh_main, wh_prod])
        db.session.commit()

        loc_main_store = Location(warehouse_id=wh_main.id, name="Main Store", code="LOC-MAIN-STORE", location_type="Internal")
        loc_rack_a = Location(warehouse_id=wh_main.id, name="Rack A", code="LOC-RACK-A", location_type="Internal")
        loc_prod_floor = Location(warehouse_id=wh_prod.id, name="Production Floor", code="LOC-PROD-FLR", location_type="Internal")
        loc_dispatch = Location(warehouse_id=wh_prod.id, name="Dispatch Area", code="LOC-DISPATCH", location_type="Internal")

        db.session.add_all([loc_main_store, loc_rack_a, loc_prod_floor, loc_dispatch])
        db.session.commit()

        print("Seeding Product Categories...")
        cat_raw = Category(name="Raw Material")
        cat_furniture = Category(name="Furniture")
        cat_safety = Category(name="Safety Equipment")

        db.session.add_all([cat_raw, cat_furniture, cat_safety])
        db.session.commit()

        print("Seeding Products & Initial Stock Balances...")
        p_steel = Product(name="Steel Rods", sku="ST-RD-001", category_id=cat_raw.id, unit="kg", reorder_level=30.0)
        p_chairs = Product(name="Office Chairs", sku="OF-CH-002", category_id=cat_furniture.id, unit="pcs", reorder_level=10.0)
        p_cement = Product(name="Cement Bags", sku="CM-BG-003", category_id=cat_raw.id, unit="bags", reorder_level=20.0)
        p_helmets = Product(name="Safety Helmets", sku="SF-HL-004", category_id=cat_safety.id, unit="pcs", reorder_level=15.0)

        db.session.add_all([p_steel, p_chairs, p_cement, p_helmets])
        db.session.commit()

        # Seed initial stock balance for steel (100 kg initial setup in Main Store)
        sb_steel = StockBalance(product_id=p_steel.id, location_id=loc_main_store.id, quantity=100.0)
        sb_chairs = StockBalance(product_id=p_chairs.id, location_id=loc_main_store.id, quantity=25.0)
        sb_cement = StockBalance(product_id=p_cement.id, location_id=loc_main_store.id, quantity=12.0)
        sb_helmets = StockBalance(product_id=p_helmets.id, location_id=loc_main_store.id, quantity=0.0)

        db.session.add_all([sb_steel, sb_chairs, sb_cement, sb_helmets])

        # Ledger entries for initial stock setup
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

        print("Executing Required Seed Stock Operations Flow...")
        # 1. Receipt: Receive 50 kg Steel Rods into Main Store
        rec1 = Receipt(reference="REC-00001", supplier_name="Apex Steel Co.", destination_location_id=loc_main_store.id, status="Draft", created_by=manager.id)
        db.session.add(rec1)
        db.session.flush()
        line1 = ReceiptLine(receipt_id=rec1.id, product_id=p_steel.id, quantity=50.0)
        db.session.add(line1)
        db.session.commit()
        validate_receipt(rec1.id, manager.id)
        print("  [OK] Validated Receipt REC-00001 (+50 kg Steel Rods)")

        # 2. Internal Transfer: Move 40 kg Steel Rods from Main Store to Production Floor
        trn1 = Transfer(reference="TRN-00001", source_location_id=loc_main_store.id, destination_location_id=loc_prod_floor.id, status="Draft", created_by=staff.id)
        db.session.add(trn1)
        db.session.flush()
        line2 = TransferLine(transfer_id=trn1.id, product_id=p_steel.id, quantity=40.0)
        db.session.add(line2)
        db.session.commit()
        validate_transfer(trn1.id, staff.id)
        print("  [OK] Validated Internal Transfer TRN-00001 (40 kg Steel Rods to Production Floor)")

        # 3. Delivery: Deliver 20 kg Steel Rods from Main Store to Customer BuildCraft Inc
        del1 = Delivery(reference="DEL-00001", customer_name="BuildCraft Inc.", source_location_id=loc_main_store.id, status="Draft", created_by=manager.id)
        db.session.add(del1)
        db.session.flush()
        line3 = DeliveryLine(delivery_id=del1.id, product_id=p_steel.id, quantity=20.0)
        db.session.add(line3)
        db.session.commit()
        validate_delivery(del1.id, manager.id)
        print("  [OK] Validated Delivery DEL-00001 (-20 kg Steel Rods)")

        # 4. Stock Adjustment: Adjust Main Store Steel Rods for 3 kg damaged stock (recorded 90, physical 87)
        adj1 = Adjustment(reference="ADJ-00001", location_id=loc_main_store.id, reason="3 kg damaged Steel Rods identified during count", status="Draft", created_by=manager.id)
        db.session.add(adj1)
        db.session.flush()
        line4 = AdjustmentLine(adjustment_id=adj1.id, product_id=p_steel.id, recorded_quantity=90.0, counted_quantity=87.0, difference=-3.0)
        db.session.add(line4)
        db.session.commit()
        validate_adjustment(adj1.id, manager.id)
        print("  [OK] Validated Stock Adjustment ADJ-00001 (-3 kg damaged Steel Rods)")

        print("Seeding Pending Stock Operations...")
        # Pending Receipt (Waiting status)
        rec2 = Receipt(reference="REC-00002", supplier_name="Global Safety Equipment Corp", destination_location_id=loc_main_store.id, status="Waiting", created_by=manager.id)
        db.session.add(rec2)
        db.session.flush()
        db.session.add(ReceiptLine(receipt_id=rec2.id, product_id=p_helmets.id, quantity=100.0))

        # Pending Delivery (Ready status)
        del2 = Delivery(reference="DEL-00002", customer_name="Metro Infrastructure Ltd", source_location_id=loc_main_store.id, status="Ready", created_by=staff.id)
        db.session.add(del2)
        db.session.flush()
        db.session.add(DeliveryLine(delivery_id=del2.id, product_id=p_cement.id, quantity=10.0))

        # Pending Transfer (Draft status)
        trn2 = Transfer(reference="TRN-00002", source_location_id=loc_main_store.id, destination_location_id=loc_dispatch.id, status="Draft", created_by=staff.id)
        db.session.add(trn2)
        db.session.flush()
        db.session.add(TransferLine(transfer_id=trn2.id, product_id=p_chairs.id, quantity=5.0))

        db.session.commit()

        print("\nDatabase seeded successfully!")
        print("="*60)
        print("Demo Credentials:")
        print("  Admin:    admin@stocksense.com    / Admin@123")
        print("  Manager:  manager@stocksense.com  / Manager@123")
        print("  Staff:    staff@stocksense.com    / Staff@123")
        print("="*60)

if __name__ == '__main__':
    seed_database()
