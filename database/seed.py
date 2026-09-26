# database/seed.py
import sys
import os
from datetime import datetime, timedelta
import random

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.supplier import Supplier
from app.models.stock import StockBalance, InventoryBatch
from app.models.ledger import StockLedger
from app.models.operation import (
    Receipt, ReceiptLine, Delivery, DeliveryLine, Transfer, TransferLine,
    Adjustment, AdjustmentLine, PutawayTask, PickTask, PurchaseOrder, PurchaseOrderItem
)
from app.models.grocery import (
    Store, ShelfLocation, FestivalEvent, FestivalProductPlan, PriceHistory,
    POSSale, POSSaleItem, ReplenishmentTask, WasteRecord
)
from app.models.ai_intelligence import (
    Forecast, SafetyStockPolicy, ReorderRecommendation, RiskEvent,
    InventoryHealthScore, Alert, AuditLog, ModelVersion
)

def seed_database():
    app = create_app('default')
    with app.app_context():
        print("Resetting and seeding StockSense Production-Grade Dual-Domain AI Database...")
        db.drop_all()
        db.create_all()

        # ==========================================
        # 1. USERS & RBAC ROLES (9 Roles)
        # ==========================================
        users = [
            User(name="Alice Administrator", email="admin@stocksense.com", role="super_admin", department="Executive"),
            User(name="Victor Warehouse Manager", email="whmanager@stocksense.com", role="warehouse_manager", department="Warehouse Operations"),
            User(name="Irene Inventory Manager", email="invmanager@stocksense.com", role="inventory_manager", department="Supply Chain"),
            User(name="Paul Procurement Manager", email="procurement@stocksense.com", role="procurement_manager", department="Procurement"),
            User(name="Oscar Warehouse Operator", email="operator@stocksense.com", role="warehouse_operator", department="Floor Operations"),
            User(name="Peter Picker Packer", email="picker@stocksense.com", role="picker_packer", department="Fulfillment"),
            User(name="Sam Supplier Representative", email="supplier@stocksense.com", role="supplier", department="External Vendor"),
            User(name="Anna AI Analyst", email="analyst@stocksense.com", role="analyst", department="Business Intelligence"),
            User(name="Arthur Compliance Auditor", email="auditor@stocksense.com", role="auditor", department="Audit & Governance")
        ]
        for u in users:
            u.set_password("StockSense@2026")
        db.session.add_all(users)
        db.session.commit()
        print("  [OK] 9 Users with RBAC roles created.")

        # ==========================================
        # 2. WAREHOUSES & LOCATION HIERARCHY
        # ==========================================
        wh1 = Warehouse(name="Main Distribution Center", code="WH-MDC-01", address="100 Industrial Boulevard, Sector 4", total_capacity_m3=8000.0, temperature_control="Standard Ambient")
        wh2 = Warehouse(name="Regional Cold Storage", code="WH-RCS-02", address="25 Frost Avenue, Cold Chain Hub", total_capacity_m3=4000.0, temperature_control="Refrigerated (2-8C)")
        wh3 = Warehouse(name="Production Hub", code="WH-PROD-03", address="500 Factory Complex, Zone B", total_capacity_m3=6000.0, temperature_control="Controlled Ambient")
        db.session.add_all([wh1, wh2, wh3])
        db.session.commit()

        locations = [
            Location(warehouse_id=wh1.id, name="Receiving Bay 1", code="MDC-RCV-01", location_type="Staging", zone="Zone A", aisle="Ais-01", rack="Rk-01", shelf="Sh-1", bin_code="Bn-01", max_capacity=1000.0, picking_frequency="High", distance_to_dispatch_m=10.0, picking_height_level=1),
            Location(warehouse_id=wh1.id, name="High-Velocity Rack A1", code="MDC-Z1-A1", location_type="Internal", zone="Zone A", aisle="Ais-01", rack="Rk-02", shelf="Sh-1", bin_code="Bn-02", max_capacity=600.0, picking_frequency="High", distance_to_dispatch_m=15.0, picking_height_level=1),
            Location(warehouse_id=wh1.id, name="Medium Storage Rack B2", code="MDC-Z2-B2", location_type="Internal", zone="Zone B", aisle="Ais-02", rack="Rk-04", shelf="Sh-2", bin_code="Bn-05", max_capacity=800.0, picking_frequency="Medium", distance_to_dispatch_m=35.0, picking_height_level=2),
            Location(warehouse_id=wh1.id, name="Upper Bulk Rack C3", code="MDC-Z3-C3", location_type="Internal", zone="Zone C", aisle="Ais-03", rack="Rk-08", shelf="Sh-4", bin_code="Bn-12", max_capacity=1200.0, picking_frequency="Low", distance_to_dispatch_m=55.0, picking_height_level=3),
            Location(warehouse_id=wh1.id, name="Dispatch Bay Alpha", code="MDC-DSP-01", location_type="Dispatch", zone="Zone D", aisle="Ais-04", rack="Rk-10", shelf="Sh-1", bin_code="Bn-01", max_capacity=500.0, picking_frequency="High", distance_to_dispatch_m=5.0, picking_height_level=1),
            
            Location(warehouse_id=wh2.id, name="Cold Zone Bin 101", code="RCS-CZ-101", location_type="Internal", zone="Cold Zone", aisle="Ais-01", rack="Rk-01", shelf="Sh-1", bin_code="Bn-01", max_capacity=400.0, temperature_condition="Cold", picking_frequency="High", distance_to_dispatch_m=20.0, picking_height_level=1),
            Location(warehouse_id=wh2.id, name="Cold Storage Rack 202", code="RCS-CZ-202", location_type="Internal", zone="Cold Zone", aisle="Ais-02", rack="Rk-02", shelf="Sh-2", bin_code="Bn-04", max_capacity=500.0, temperature_condition="Cold", picking_frequency="Medium", distance_to_dispatch_m=30.0, picking_height_level=2),
            
            Location(warehouse_id=wh3.id, name="Production Floor Staging", code="PRD-FLR-01", location_type="Internal", zone="Fast Pick", aisle="Ais-01", rack="Rk-01", shelf="Sh-1", bin_code="Bn-01", max_capacity=1500.0, picking_frequency="High", distance_to_dispatch_m=12.0, picking_height_level=1)
        ]
        db.session.add_all(locations)
        db.session.commit()
        print("  [OK] Warehouses & Location Hierarchy seeded.")

        # ==========================================
        # 3. GROCERY RETAIL STORES & SHELVES
        # ==========================================
        store1 = Store(name="Flagship Supermarket", code="STR-01", store_type="Supermarket", address="Downtown Central Plaza", manager_name="Irene Manager")
        store2 = Store(name="Hypermarket Metro", code="STR-02", store_type="Hypermarket", address="Westside Retail Hub", manager_name="Victor Manager")
        store3 = Store(name="Dark Store Express", code="STR-03", store_type="Dark Store", address="Logistics Ring Road", manager_name="Oscar Operator")
        db.session.add_all([store1, store2, store3])
        db.session.commit()

        shelves = [
            ShelfLocation(store_id=store1.id, aisle="Aisle 1 Dairy", shelf_code="SH-DAIRY-01", capacity=100.0, current_occupancy=45.0, temperature_zone="Cold"),
            ShelfLocation(store_id=store1.id, aisle="Aisle 2 Fresh Produce", shelf_code="SH-PROD-02", capacity=150.0, current_occupancy=80.0, temperature_zone="Ambient"),
            ShelfLocation(store_id=store1.id, aisle="Aisle 3 Gifting & Sweets", shelf_code="SH-SWT-03", capacity=120.0, current_occupancy=90.0, temperature_zone="Ambient")
        ]
        db.session.add_all(shelves)
        db.session.commit()
        print("  [OK] Grocery Retail Stores & Shelves seeded.")

        # ==========================================
        # 4. CATEGORIES & MASTER CATALOG (12 SKUs)
        # ==========================================
        cat_raw = Category(name="Raw Materials", description="Industrial raw inputs and structural stock")
        cat_elec = Category(name="Electronics", description="High-value microchips and controllers")
        cat_pharma = Category(name="Perishables & Pharma", description="Temperature-sensitive inventory")
        cat_dairy = Category(name="Fresh Dairy & Produce", description="Perishable grocery essentials")
        cat_festive = Category(name="Festival Gifting & Sweets", description="Seasonal festival specials")
        db.session.add_all([cat_raw, cat_elec, cat_pharma, cat_dairy, cat_festive])
        db.session.commit()

        products = [
            # Warehouse SKUs
            Product(name="High-Grade Steel Rods", sku="ST-RD-001", barcode="890123456710", category_id=cat_raw.id, unit="kg", unit_cost=120.0, selling_price=180.0, mrp=199.0, reorder_level=40.0, lead_time_days=4, abc_class="A", xyz_class="X", velocity_class="F", is_critical=True, weight_kg=5.0, volume_m3=0.02),
            Product(name="ARM Cortex Microcontrollers", sku="EL-MC-002", barcode="890123456711", category_id=cat_elec.id, unit="pcs", unit_cost=450.0, selling_price=650.0, mrp=699.0, reorder_level=15.0, lead_time_days=7, abc_class="A", xyz_class="Y", velocity_class="F", is_critical=True, is_fragile=True, weight_kg=0.2, volume_m3=0.001),
            Product(name="Industrial Cement Bags", sku="CM-BG-003", barcode="890123456712", category_id=cat_raw.id, unit="bags", unit_cost=18.0, selling_price=30.0, mrp=35.0, reorder_level=50.0, lead_time_days=3, abc_class="B", xyz_class="X", velocity_class="F", weight_kg=50.0, volume_m3=0.05),
            Product(name="Insulin Refrigerated Vials", sku="PH-IN-004", barcode="890123456713", category_id=cat_pharma.id, unit="vials", unit_cost=85.0, selling_price=140.0, mrp=150.0, reorder_level=25.0, lead_time_days=2, abc_class="A", xyz_class="Z", velocity_class="F", is_critical=True, is_expiry_sensitive=True, temperature_requirement="Cold", shelf_life_days=60, weight_kg=0.1, volume_m3=0.0005),
            
            # Grocery Retail SKUs
            Product(name="Organic Whole Milk 1L", sku="DAIRY-MILK-1L", barcode="890123456701", plu_code="4011", brand="NatureFresh", category_id=cat_dairy.id, unit="liter", unit_cost=2.80, selling_price=4.50, mrp=4.99, reorder_level=20.0, shelf_stock=30.0, backroom_stock=50.0, shelf_capacity=60.0, is_perishable=True, is_expiry_sensitive=True, freshness_days=10, shelf_life_days=10),
            Product(name="Fresh Alphonso Mangoes 1kg", sku="PROD-MANGO-1KG", barcode="890123456702", plu_code="4012", brand="FarmDirect", category_id=cat_dairy.id, unit="kg", unit_cost=6.00, selling_price=9.99, mrp=11.99, reorder_level=15.0, shelf_stock=20.0, backroom_stock=40.0, shelf_capacity=40.0, is_perishable=True, is_expiry_sensitive=True, freshness_days=7, shelf_life_days=7),
            Product(name="Diwali Premium Sweet Box 500g", sku="FEST-SWEET-500G", barcode="890123456703", brand="RoyalSweets", category_id=cat_festive.id, unit="box", unit_cost=8.50, selling_price=14.99, mrp=17.99, promotion_price=13.99, reorder_level=30.0, shelf_stock=45.0, backroom_stock=80.0, shelf_capacity=50.0, is_perishable=True, freshness_days=25, shelf_life_days=25),
            Product(name="Basmati Premium Rice 5kg", sku="GR-RICE-5KG", barcode="890123456704", brand="RoyalGrains", category_id=cat_dairy.id, unit="bag", unit_cost=12.00, selling_price=18.99, mrp=21.99, reorder_level=10.0, shelf_stock=15.0, backroom_stock=35.0, shelf_capacity=25.0, is_perishable=False, freshness_days=365, shelf_life_days=365)
        ]
        db.session.add_all(products)
        db.session.commit()
        print("  [OK] Products & Master Catalog seeded.")

        # ==========================================
        # 5. SUPPLIERS & SCORECARDS
        # ==========================================
        sup1 = Supplier(name="Apex Steel Industries", code="SUP-APEX", contact_email="orders@apexsteel.com", lead_time_days=4, lead_time_variance_days=0.5, on_time_delivery_rate=98.0, fill_rate_pct=99.0, quality_acceptance_rate=98.5, supplier_score=97.0, classification="Strategic")
        sup2 = Supplier(name="Silicon Microtech Corp", code="SUP-SILICON", contact_email="sales@siliconmicro.com", lead_time_days=7, lead_time_variance_days=1.2, on_time_delivery_rate=94.0, fill_rate_pct=96.0, quality_acceptance_rate=95.0, supplier_score=94.0, classification="Reliable")
        sup3 = Supplier(name="BioCold Pharma Logistics", code="SUP-BIOCOLD", contact_email="supply@biocold.com", lead_time_days=2, lead_time_variance_days=0.2, on_time_delivery_rate=99.5, fill_rate_pct=100.0, quality_acceptance_rate=99.0, supplier_score=99.0, classification="Strategic")
        sup4 = Supplier(name="Global Safety Products", code="SUP-GLOBAL", contact_email="orders@globalsafety.com", lead_time_days=6, lead_time_variance_days=2.5, on_time_delivery_rate=82.0, fill_rate_pct=88.0, quality_acceptance_rate=90.0, supplier_score=84.0, classification="Monitor")
        db.session.add_all([sup1, sup2, sup3, sup4])
        db.session.commit()
        print("  [OK] Suppliers & Performance Scorecards seeded.")

        # ==========================================
        # 6. INITIAL STOCK BALANCES & BATCHES
        # ==========================================
        now = datetime.utcnow()
        loc_main = locations[1] # High-Velocity Rack A1
        loc_cold = locations[5] # Cold Zone Bin 101

        balances = [
            StockBalance(product_id=products[0].id, location_id=loc_main.id, quantity=180.0, reserved_quantity=20.0, batch_number="BATCH-ST-2026A", expiry_date=now + timedelta(days=365)),
            StockBalance(product_id=products[1].id, location_id=loc_main.id, quantity=35.0, reserved_quantity=5.0, batch_number="BATCH-EL-2026B", expiry_date=now + timedelta(days=730)),
            StockBalance(product_id=products[2].id, location_id=loc_main.id, quantity=12.0, reserved_quantity=0.0, batch_number="BATCH-CM-2026C", expiry_date=now + timedelta(days=15)),
            StockBalance(product_id=products[3].id, location_id=loc_cold.id, quantity=80.0, reserved_quantity=10.0, batch_number="BATCH-PH-2026D", expiry_date=now + timedelta(days=20)),
            StockBalance(product_id=products[4].id, location_id=loc_cold.id, quantity=80.0, reserved_quantity=0.0, batch_number="BATCH-MILK-2026E", expiry_date=now + timedelta(days=6)),
            StockBalance(product_id=products[5].id, location_id=loc_main.id, quantity=60.0, reserved_quantity=0.0, batch_number="BATCH-MNG-2026F", expiry_date=now + timedelta(days=4)),
            StockBalance(product_id=products[6].id, location_id=loc_main.id, quantity=125.0, reserved_quantity=10.0, batch_number="BATCH-SWT-2026G", expiry_date=now + timedelta(days=20))
        ]
        db.session.add_all(balances)
        db.session.commit()

        batches = [
            InventoryBatch(batch_number="BATCH-ST-2026A", product_id=products[0].id, location_id=loc_main.id, supplier_id=sup1.id, initial_quantity=200.0, current_quantity=180.0, unit_cost=120.0, expiry_date=now + timedelta(days=365)),
            InventoryBatch(batch_number="BATCH-MILK-2026E", product_id=products[4].id, location_id=loc_cold.id, supplier_id=sup3.id, initial_quantity=100.0, current_quantity=80.0, unit_cost=2.80, expiry_date=now + timedelta(days=6)),
            InventoryBatch(batch_number="BATCH-SWT-2026G", product_id=products[6].id, location_id=loc_main.id, supplier_id=sup4.id, initial_quantity=150.0, current_quantity=125.0, unit_cost=8.50, expiry_date=now + timedelta(days=20))
        ]
        db.session.add_all(batches)
        db.session.commit()
        print("  [OK] Stock Balances & Batches seeded.")

        # ==========================================
        # 7. HISTORICAL TIME SERIES (90-DAY STOCK LEDGER)
        # ==========================================
        print("  [OK] Generating 90-day time-series history for AI Demand Forecasting model training...")
        start_history = now - timedelta(days=90)
        admin_user = users[0]

        for day_offset in range(90):
            txn_date = start_history + timedelta(days=day_offset)
            for p in products:
                if random.random() > 0.3:
                    daily_sales_qty = round(random.uniform(2.0, 15.0), 1)
                    ledger = StockLedger(
                        transaction_id=f"TXN-HIST-{day_offset:02d}-{p.sku}",
                        product_id=p.id,
                        batch_number="BATCH-2026-HIST",
                        source_location_id=loc_main.id,
                        operation_type='Sale dispatch',
                        reference=f"SO-HIST-{1000+day_offset}",
                        quantity_change=-daily_sales_qty,
                        quantity_before=100.0,
                        quantity_after=100.0 - daily_sales_qty,
                        unit_cost=p.unit_cost,
                        total_value_change=round(-daily_sales_qty * p.unit_cost, 2),
                        reason="Historical Sales Outflow",
                        created_by=admin_user.id,
                        created_at=txn_date
                    )
                    db.session.add(ledger)

        db.session.commit()

        # ==========================================
        # 8. POS SALES, PRICE HISTORY & WASTE LOGS
        # ==========================================
        pos_sale1 = POSSale(receipt_number="POS-2026-0001", store_id=store1.id, total_amount=22.50, payment_method="Credit Card", cashier_id=users[4].id)
        db.session.add(pos_sale1)
        db.session.flush()
        db.session.add(POSSaleItem(sale_id=pos_sale1.id, product_id=products[4].id, quantity=5.0, unit_price=4.50, subtotal=22.50))

        waste1 = WasteRecord(record_code="WST-2026-001", store_id=store1.id, product_id=products[4].id, quantity=4.0, total_cost_waste=11.20, reason="Expired", recorded_by_id=users[2].id)
        db.session.add(waste1)

        ph1 = PriceHistory(product_id=products[6].id, old_price=17.99, new_price=14.99, price_type="Promotion", rationale="Diwali Festive Promotion Uplift", changed_by_id=users[3].id)
        db.session.add(ph1)

        db.session.commit()
        print("  [OK] POS Sales, Price History & Waste Logs seeded.")

        # ==========================================
        # 9. FESTIVAL EVENTS & PRODUCT PLANS
        # ==========================================
        today_date = now.date()
        f_diwali = FestivalEvent(
            name="Diwali Mega Sale",
            code="FEST-DIWALI-2026",
            start_date=today_date,
            end_date=today_date + timedelta(days=7),
            prep_start_date=today_date - timedelta(days=7),
            post_clearance_end_date=today_date + timedelta(days=14),
            category_focus="Sweets, Gifting, Grocery Essentials",
            expected_demand_uplift_pct=150.0,
            status="ACTIVE"
        )
        db.session.add(f_diwali)
        db.session.commit()

        f_plan = FestivalProductPlan(
            festival_id=f_diwali.id,
            product_id=products[6].id,
            store_id=store1.id,
            baseline_daily_demand=15.0,
            forecast_uplift_pct=150.0,
            recommended_procurement_qty=250.0,
            safety_stock_buffer=40.0,
            promotion_price=13.99,
            expected_revenue=3497.50,
            expected_margin_pct=43.3,
            status="Approved"
        )
        db.session.add(f_plan)
        db.session.commit()
        print("  [OK] Festival Events & Product Plans seeded.")

        # ==========================================
        # 10. AI REORDER RECOMMENDATIONS, RISKS & ALERTS
        # ==========================================
        rec1 = ReorderRecommendation(
            rec_code="REC-2026-001",
            product_id=products[4].id,
            warehouse_id=wh1.id,
            supplier_id=sup3.id,
            current_stock=30.0,
            forecasted_demand_30d=150.0,
            safety_stock=25.0,
            reorder_point=45.0,
            recommended_action="Reorder",
            recommended_quantity=100.0,
            problem_detected="Milk inventory below reorder point (45 units). Stockout expected in 2 days.",
            predicted_impact="Prevents $675 revenue loss and maintains 98% shelf availability.",
            urgency_level="CRITICAL",
            confidence_level_pct=95.0,
            financial_impact=280.0,
            approval_status="Generated"
        )
        db.session.add(rec1)

        risk1 = RiskEvent(
            risk_code="RSK-2026-001",
            product_id=products[4].id,
            risk_category="Expiry",
            severity="High",
            probability_pct=85.0,
            predicted_date=now + timedelta(days=6),
            quantity_affected=15.0,
            financial_impact=42.0,
            recommended_action="Apply 30% Dynamic Markdown or Prioritize FEFO Shelf Picking",
            status="Active"
        )
        db.session.add(risk1)

        alert1 = Alert(
            alert_type="Expiry_Warning",
            severity="High",
            title="Near-Expiry Perishable Stock Detected",
            message="Organic Whole Milk 1L (Batch BATCH-MILK-2026E) expires in 6 days.",
            product_id=products[4].id,
            status="Open"
        )
        db.session.add(alert1)

        # Audit Log
        db.session.add(AuditLog(action_type="System_Init", entity_name="Database", entity_id="1", description="StockSense Production-Grade Dual-Domain AI Database initialized.", performed_by=admin_user.id))

        db.session.commit()
        print("  [OK] Operational Tasks, AI Reorder Recs, Risks, and Audit Logs seeded.")
        print("="*70)
        print("StockSense Complete Database Seeding Successful! All features ready.")
        print("="*70)

if __name__ == '__main__':
    seed_database()
