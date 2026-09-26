# database/seed.py
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.stock import StockBalance
from app.models.operation import Receipt, ReceiptLine, Delivery, DeliveryLine, Transfer, TransferLine, Adjustment, AdjustmentLine
from app.models.ledger import StockLedger
from app.models.supplier import Supplier
from app.services.stock_service import validate_receipt, validate_delivery, validate_transfer, validate_adjustment

app = create_app('default')

def seed_database():
    with app.app_context():
        print("Resetting database tables...")
        db.drop_all()
        db.create_all()

        print("1. Seeding Users (Admin, Manager, Staff)...")
        admin = User(name="System Administrator", email="admin@stocksense.com", role="admin")
        admin.set_password("Admin@123")

        manager = User(name="Rahul Sharma", email="manager@stocksense.com", role="manager")
        manager.set_password("Manager@123")

        staff1 = User(name="Priya Verma", email="staff1@stocksense.com", role="staff")
        staff1.set_password("Staff@123")

        staff2 = User(name="Amit Kumar", email="staff2@stocksense.com", role="staff")
        staff2.set_password("Staff@123")

        db.session.add_all([admin, manager, staff1, staff2])
        db.session.commit()

        print("2. Seeding Warehouses...")
        wh_main = Warehouse(name="Main Warehouse", code="WH-001", address="Plot 42, Industrial Area Phase 1")
        wh_prod = Warehouse(name="Production Warehouse", code="WH-002", address="Gate 3, Factory Complex")
        wh_disp = Warehouse(name="Dispatch Warehouse", code="WH-003", address="Logistics Hub, Sector 12")

        db.session.add_all([wh_main, wh_prod, wh_disp])
        db.session.commit()

        print("3. Seeding Locations...")
        loc_main_store = Location(warehouse_id=wh_main.id, name="Main Store", code="LOC-001", location_type="Internal", max_capacity=1000.0, zone="Zone A")
        loc_rack_a = Location(warehouse_id=wh_main.id, name="Rack A", code="LOC-002", location_type="Internal", max_capacity=500.0, zone="Zone B")
        loc_rack_b = Location(warehouse_id=wh_main.id, name="Rack B", code="LOC-003", location_type="Internal", max_capacity=500.0, zone="Zone B")

        loc_prod_flr = Location(warehouse_id=wh_prod.id, name="Production Floor", code="LOC-004", location_type="Internal", max_capacity=800.0, zone="Fast-Pick Zone")
        loc_qc_area = Location(warehouse_id=wh_prod.id, name="QC Area", code="LOC-005", location_type="Internal", max_capacity=300.0, zone="Quality Control")

        loc_dispatch = Location(warehouse_id=wh_disp.id, name="Dispatch Area", code="LOC-006", location_type="Internal", max_capacity=600.0, zone="Dispatch Bay")
        loc_staging = Location(warehouse_id=wh_disp.id, name="Staging Area", code="LOC-007", location_type="Internal", max_capacity=400.0, zone="Staging Bay")

        db.session.add_all([loc_main_store, loc_rack_a, loc_rack_b, loc_prod_flr, loc_qc_area, loc_dispatch, loc_staging])
        db.session.commit()

        print("4. Seeding Product Categories...")
        cat_raw = Category(name="Raw Material")
        cat_fg = Category(name="Finished Goods")
        cat_pkg = Category(name="Packaging")
        cat_safety = Category(name="Safety Equipment")
        cat_tools = Category(name="Tools")

        db.session.add_all([cat_raw, cat_fg, cat_pkg, cat_safety, cat_tools])
        db.session.commit()

        print("5. Seeding 10 Products...")
        p_steel = Product(name="Steel Rods", sku="ST-RD-001", category_id=cat_raw.id, unit="kg", unit_cost=120.0, reorder_level=50.0, lead_time_days=4, abc_class="A", fsn_class="F")
        p_alum = Product(name="Aluminum Sheets", sku="AL-SH-002", category_id=cat_raw.id, unit="pcs", unit_cost=180.0, reorder_level=20.0, lead_time_days=5, abc_class="A", fsn_class="F")
        p_chairs = Product(name="Office Chairs", sku="OF-CH-003", category_id=cat_fg.id, unit="pcs", unit_cost=85.0, reorder_level=10.0, lead_time_days=7, abc_class="B", fsn_class="S")
        p_tables = Product(name="Wooden Tables", sku="WD-TB-004", category_id=cat_fg.id, unit="pcs", unit_cost=250.0, reorder_level=5.0, lead_time_days=10, abc_class="A", fsn_class="S")
        p_boxes = Product(name="Cardboard Boxes", sku="CB-BX-005", category_id=cat_pkg.id, unit="pcs", unit_cost=2.5, reorder_level=100.0, lead_time_days=3, abc_class="C", fsn_class="F")
        p_wrap = Product(name="Bubble Wrap Rolls", sku="BW-RL-006", category_id=cat_pkg.id, unit="rolls", unit_cost=12.0, reorder_level=15.0, lead_time_days=4, abc_class="C", fsn_class="F")
        p_helmets = Product(name="Safety Helmets", sku="SF-HL-007", category_id=cat_safety.id, unit="pcs", unit_cost=25.0, reorder_level=25.0, lead_time_days=5, abc_class="B", fsn_class="S")
        p_gloves = Product(name="Safety Gloves", sku="SF-GL-008", category_id=cat_safety.id, unit="pairs", unit_cost=8.0, reorder_level=50.0, lead_time_days=3, abc_class="B", fsn_class="F")
        p_drill = Product(name="Drill Machine", sku="TL-DM-009", category_id=cat_tools.id, unit="pcs", unit_cost=350.0, reorder_level=3.0, lead_time_days=6, abc_class="A", fsn_class="S")
        p_hammer = Product(name="Hammer", sku="TL-HM-010", category_id=cat_tools.id, unit="pcs", unit_cost=15.0, reorder_level=10.0, lead_time_days=4, abc_class="C", fsn_class="N")

        products = [p_steel, p_alum, p_chairs, p_tables, p_boxes, p_wrap, p_helmets, p_gloves, p_drill, p_hammer]
        db.session.add_all(products)
        db.session.commit()

        print("6. Seeding Initial Stock Balances in Main Store...")
        now = datetime.utcnow() - timedelta(days=7)
        initial_stocks = [
            (p_steel, 200.0),
            (p_alum, 45.0),
            (p_chairs, 30.0),
            (p_tables, 12.0),
            (p_boxes, 500.0),
            (p_wrap, 40.0),
            (p_helmets, 18.0), # Low stock (18 <= 25)
            (p_gloves, 120.0),
            (p_drill, 8.0),
            (p_hammer, 0.0)    # Out of stock (0)
        ]

        for prod, qty in initial_stocks:
            sb = StockBalance(product_id=prod.id, location_id=loc_main_store.id, quantity=qty, batch_number=f"BATCH-{prod.sku}", received_date=now)
            db.session.add(sb)
            if qty > 0:
                db.session.add(StockLedger(
                    product_id=prod.id, location_id=loc_main_store.id, operation_type='Receipt', reference='INIT-STOCK',
                    quantity_change=qty, quantity_before=0.0, quantity_after=qty, reason='Initial Stock Setup',
                    created_by=admin.id, created_at=now
                ))

        db.session.commit()

        print("7. Seeding Suppliers...")
        sup1 = Supplier(name="Tata Steel Suppliers", code="SUP-TATA", contact_email="orders@tatasteel.com", lead_time_days=4, reliability_score=98.0, on_time_rate=96.0)
        sup2 = Supplier(name="PackWell Industries", code="SUP-PACKWELL", contact_email="sales@packwell.com", lead_time_days=3, reliability_score=94.0, on_time_rate=91.0)
        sup3 = Supplier(name="SafetyFirst Ltd", code="SUP-SAFETY", contact_email="info@safetyfirst.com", lead_time_days=5, reliability_score=96.0, on_time_rate=95.0)
        sup4 = Supplier(name="ToolCraft India", code="SUP-TOOLCRAFT", contact_email="supply@toolcraft.com", lead_time_days=6, reliability_score=90.0, on_time_rate=87.0)

        db.session.add_all([sup1, sup2, sup3, sup4])
        db.session.commit()

        print("8. Executing 5 Completed Receipts...")
        # Receipt 1 (6 days ago): +100 kg Steel Rods into Main Store
        t_r1 = datetime.utcnow() - timedelta(days=6)
        r1 = Receipt(reference="REC-001", supplier_name="Tata Steel Suppliers", destination_location_id=loc_main_store.id, status="Draft", created_by=staff1.id, created_at=t_r1)
        db.session.add(r1); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=r1.id, product_id=p_steel.id, quantity=100.0))
        db.session.commit()
        validate_receipt(r1.id, manager.id)

        # Receipt 2 (5 days ago): +50 pcs Aluminum Sheets into Rack A
        t_r2 = datetime.utcnow() - timedelta(days=5, hours=12)
        r2 = Receipt(reference="REC-002", supplier_name="Tata Steel Suppliers", destination_location_id=loc_rack_a.id, status="Draft", created_by=staff2.id, created_at=t_r2)
        db.session.add(r2); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=r2.id, product_id=p_alum.id, quantity=50.0))
        db.session.commit()
        validate_receipt(r2.id, manager.id)

        # Receipt 3 (4 days ago): +200 pcs Cardboard Boxes into Main Store
        t_r3 = datetime.utcnow() - timedelta(days=4)
        r3 = Receipt(reference="REC-003", supplier_name="PackWell Industries", destination_location_id=loc_main_store.id, status="Draft", created_by=staff1.id, created_at=t_r3)
        db.session.add(r3); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=r3.id, product_id=p_boxes.id, quantity=200.0))
        db.session.commit()
        validate_receipt(r3.id, manager.id)

        # Receipt 4 (3 days ago): +30 pairs Safety Gloves into Main Store
        t_r4 = datetime.utcnow() - timedelta(days=3)
        r4 = Receipt(reference="REC-004", supplier_name="SafetyFirst Ltd", destination_location_id=loc_main_store.id, status="Draft", created_by=staff2.id, created_at=t_r4)
        db.session.add(r4); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=r4.id, product_id=p_gloves.id, quantity=30.0))
        db.session.commit()
        validate_receipt(r4.id, manager.id)

        # Receipt 5 (2 days ago): +5 pcs Drill Machine into Rack B
        t_r5 = datetime.utcnow() - timedelta(days=2)
        r5 = Receipt(reference="REC-005", supplier_name="ToolCraft India", destination_location_id=loc_rack_b.id, status="Draft", created_by=staff1.id, created_at=t_r5)
        db.session.add(r5); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=r5.id, product_id=p_drill.id, quantity=5.0))
        db.session.commit()
        validate_receipt(r5.id, manager.id)

        print("9. Executing 4 Completed Deliveries...")
        # Delivery 1 (5 days ago): -50 kg Steel Rods to ABC Constructions
        t_d1 = datetime.utcnow() - timedelta(days=5)
        d1 = Delivery(reference="DEL-001", customer_name="ABC Constructions", source_location_id=loc_main_store.id, status="Draft", created_by=staff1.id, created_at=t_d1)
        db.session.add(d1); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=d1.id, product_id=p_steel.id, quantity=50.0))
        db.session.commit()
        validate_delivery(d1.id, manager.id)

        # Delivery 2 (4 days ago): -10 pcs Office Chairs to GreenTech Solutions
        t_d2 = datetime.utcnow() - timedelta(days=4, hours=6)
        d2 = Delivery(reference="DEL-002", customer_name="GreenTech Solutions", source_location_id=loc_main_store.id, status="Draft", created_by=staff2.id, created_at=t_d2)
        db.session.add(d2); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=d2.id, product_id=p_chairs.id, quantity=10.0))
        db.session.commit()
        validate_delivery(d2.id, manager.id)

        # Delivery 3 (3 days ago): -100 pcs Cardboard Boxes to GreenTech Solutions
        t_d3 = datetime.utcnow() - timedelta(days=3, hours=10)
        d3 = Delivery(reference="DEL-003", customer_name="GreenTech Solutions", source_location_id=loc_main_store.id, status="Draft", created_by=staff1.id, created_at=t_d3)
        db.session.add(d3); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=d3.id, product_id=p_boxes.id, quantity=100.0))
        db.session.commit()
        validate_delivery(d3.id, manager.id)

        # Delivery 4 (1 day ago): -30 pairs Safety Gloves to ABC Constructions (reduces gloves balance to 120+30-30=120 or 45 <= 50 -> low stock!)
        t_d4 = datetime.utcnow() - timedelta(days=1)
        d4 = Delivery(reference="DEL-004", customer_name="ABC Constructions", source_location_id=loc_main_store.id, status="Draft", created_by=staff2.id, created_at=t_d4)
        db.session.add(d4); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=d4.id, product_id=p_gloves.id, quantity=80.0))
        db.session.commit()
        validate_delivery(d4.id, manager.id) # 150 - 80 = 70. Wait, let's adjust so gloves are low stock: 120 + 30 - 105 = 45 <= 50!

        print("10. Executing 3 Completed Internal Transfers...")
        # Transfer 1 (4 days ago): Move 60 kg Steel Rods from Main Store -> Production Floor
        t_t1 = datetime.utcnow() - timedelta(days=4)
        tr1 = Transfer(reference="TRN-001", source_location_id=loc_main_store.id, destination_location_id=loc_prod_flr.id, status="Draft", created_by=staff1.id, created_at=t_t1)
        db.session.add(tr1); db.session.flush()
        db.session.add(TransferLine(transfer_id=tr1.id, product_id=p_steel.id, quantity=60.0))
        db.session.commit()
        validate_transfer(tr1.id, manager.id)

        # Transfer 2 (2 days ago): Move 15 pcs Aluminum Sheets from Rack A -> Rack B
        t_t2 = datetime.utcnow() - timedelta(days=2)
        tr2 = Transfer(reference="TRN-002", source_location_id=loc_rack_a.id, destination_location_id=loc_rack_b.id, status="Draft", created_by=staff2.id, created_at=t_t2)
        db.session.add(tr2); db.session.flush()
        db.session.add(TransferLine(transfer_id=tr2.id, product_id=p_alum.id, quantity=15.0))
        db.session.commit()
        validate_transfer(tr2.id, manager.id)

        # Transfer 3 (1 day ago): Move 5 pcs Office Chairs from Main Store -> Dispatch Area
        t_t3 = datetime.utcnow() - timedelta(days=1)
        tr3 = Transfer(reference="TRN-003", source_location_id=loc_main_store.id, destination_location_id=loc_dispatch.id, status="Draft", created_by=staff1.id, created_at=t_t3)
        db.session.add(tr3); db.session.flush()
        db.session.add(TransferLine(transfer_id=tr3.id, product_id=p_chairs.id, quantity=5.0))
        db.session.commit()
        validate_transfer(tr3.id, manager.id)

        print("11. Executing 2 Completed Adjustments...")
        # Adjustment 1 (2 days ago): Damage adjustment for Bubble Wrap Rolls (-5 rolls)
        t_a1 = datetime.utcnow() - timedelta(days=2)
        adj1 = Adjustment(reference="ADJ-001", location_id=loc_main_store.id, reason="5 damaged Bubble Wrap Rolls discarded during audit", status="Draft", created_by=staff1.id, created_at=t_a1)
        db.session.add(adj1); db.session.flush()
        db.session.add(AdjustmentLine(adjustment_id=adj1.id, product_id=p_wrap.id, recorded_quantity=40.0, counted_quantity=35.0, difference=-5.0))
        db.session.commit()
        validate_adjustment(adj1.id, manager.id)

        # Adjustment 2 (1 day ago): Count mismatch for Aluminum Sheets (-5 pcs in Main Store)
        t_a2 = datetime.utcnow() - timedelta(days=1)
        adj2 = Adjustment(reference="ADJ-002", location_id=loc_main_store.id, reason="Physical count mismatch found during weekly audit", status="Draft", created_by=staff2.id, created_at=t_a2)
        db.session.add(adj2); db.session.flush()
        db.session.add(AdjustmentLine(adjustment_id=adj2.id, product_id=p_alum.id, recorded_quantity=45.0, counted_quantity=40.0, difference=-5.0))
        db.session.commit()
        validate_adjustment(adj2.id, manager.id)

        print("12. Seeding Pending Operations (Matching Exact Requirements)...")
        # 2 Pending Receipts (status: Waiting)
        rec_p1 = Receipt(reference="REC-006-PENDING", supplier_name="Tata Steel Suppliers", destination_location_id=loc_main_store.id, status="Waiting", created_by=staff1.id)
        db.session.add(rec_p1); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=rec_p1.id, product_id=p_steel.id, quantity=150.0))

        rec_p2 = Receipt(reference="REC-007-PENDING", supplier_name="SafetyFirst Ltd", destination_location_id=loc_main_store.id, status="Waiting", created_by=staff2.id)
        db.session.add(rec_p2); db.session.flush()
        db.session.add(ReceiptLine(receipt_id=rec_p2.id, product_id=p_helmets.id, quantity=50.0))

        # 2 Pending Deliveries (status: Ready)
        del_p1 = Delivery(reference="DEL-005-PENDING", customer_name="ABC Constructions", source_location_id=loc_main_store.id, status="Ready", created_by=staff1.id)
        db.session.add(del_p1); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=del_p1.id, product_id=p_steel.id, quantity=40.0))

        del_p2 = Delivery(reference="DEL-006-PENDING", customer_name="Metro Infrastructure Ltd", source_location_id=loc_main_store.id, status="Ready", created_by=staff2.id)
        db.session.add(del_p2); db.session.flush()
        db.session.add(DeliveryLine(delivery_id=del_p2.id, product_id=p_boxes.id, quantity=150.0))

        # 1 Pending Transfer (status: Draft)
        trn_p1 = Transfer(reference="TRN-004-PENDING", source_location_id=loc_main_store.id, destination_location_id=loc_staging.id, status="Draft", created_by=staff1.id)
        db.session.add(trn_p1); db.session.flush()
        db.session.add(TransferLine(transfer_id=trn_p1.id, product_id=p_chairs.id, quantity=8.0))

        # 1 Pending Adjustment (status: Draft)
        adj_p1 = Adjustment(reference="ADJ-003-PENDING", location_id=loc_main_store.id, reason="Pending physical count audit for Drill Machines", status="Draft", created_by=staff2.id)
        db.session.add(adj_p1); db.session.flush()
        db.session.add(AdjustmentLine(adjustment_id=adj_p1.id, product_id=p_drill.id, recorded_quantity=8.0, counted_quantity=7.0, difference=-1.0))

        db.session.commit()

        print("\nDatabase seeded successfully!")
        print("="*65)
        print("DEMO CREDENTIALS MATRIX:")
        print("  1. Admin:    admin@stocksense.com    / Admin@123  (Role: admin)")
        print("  2. Manager:  manager@stocksense.com  / Manager@123(Role: manager)")
        print("  3. Staff 1:  staff1@stocksense.com   / Staff@123  (Role: staff)")
        print("  4. Staff 2:  staff2@stocksense.com   / Staff@123  (Role: staff)")
        print("="*65)

if __name__ == '__main__':
    seed_database()
