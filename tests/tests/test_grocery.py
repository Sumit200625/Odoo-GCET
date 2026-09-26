# tests/test_grocery.py
import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.stock import StockBalance
from app.models.grocery import Store, FestivalEvent, PriceHistory
from app.services.grocery_intelligence_service import (
    record_pos_checkout_sale,
    record_waste_disposal,
    get_grocery_dashboard_data
)
from app.services.festival_planning_service import (
    get_active_and_upcoming_festivals,
    run_11_step_festival_planning_wizard,
    execute_post_festival_clearance
)
from app.services.price_intelligence_service import update_product_price, recommend_near_expiry_markdown
from app.services.scan_intelligence_service import process_scanned_barcode
from app.services.assistant_service import process_assistant_natural_language_query

class GroceryIntelligenceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.user = User(name="Store Manager", email="manager@stocksense.com", role="grocery_manager")
        self.user.set_password("pass")
        db.session.add(self.user)

        self.wh = Warehouse(name="Central Warehouse", code="WH-01")
        db.session.add(self.wh)
        db.session.commit()

        self.loc = Location(warehouse_id=self.wh.id, name="Main Storage", code="WH01-MAIN")
        db.session.add(self.loc)

        self.cat = Category(name="Fresh Dairy")
        db.session.add(self.cat)
        db.session.commit()

        self.store = Store(name="Flagship Supermarket", code="STR-01", address="Downtown")
        db.session.add(self.store)
        db.session.commit()

        self.product = Product(
            name="Organic Whole Milk 1L",
            sku="DAIRY-MILK-1L",
            barcode="890123456701",
            category_id=self.cat.id,
            unit="liter",
            reorder_level=20.0,
            selling_price=4.50,
            unit_cost=2.80,
            mrp=4.99,
            shelf_stock=30.0,
            backroom_stock=50.0,
            shelf_capacity=60.0,
            is_perishable=True,
            freshness_days=10
        )
        db.session.add(self.product)
        db.session.commit()

        sb = StockBalance(product_id=self.product.id, location_id=self.loc.id, quantity=100.0)
        db.session.add(sb)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_pos_checkout_sale(self):
        items = [{'product_id': self.product.id, 'quantity': 5.0}]
        sale = record_pos_checkout_sale(self.store.id, items, self.user.id)
        
        self.assertIsNotNone(sale)
        self.assertEqual(sale.total_amount, 22.50)
        
        # Verify shelf stock deducted from 30 -> 25
        db.session.refresh(self.product)
        self.assertEqual(self.product.shelf_stock, 25.0)

    def test_waste_disposal_logging(self):
        waste = record_waste_disposal(self.product.id, 4.0, "Expired", self.user.id)
        
        self.assertIsNotNone(waste)
        self.assertEqual(waste.total_cost_waste, 11.20) # 4 * 2.80
        
        # Verify shelf stock deducted from 30 -> 26
        db.session.refresh(self.product)
        self.assertEqual(self.product.shelf_stock, 26.0)

    def test_festival_planning_wizard(self):
        now = datetime.now().date()
        event = FestivalEvent(
            name="Diwali Mega Sale",
            code="FEST-DIWALI-2026",
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=12),
            prep_start_date=now,
            post_clearance_end_date=now + timedelta(days=20),
            expected_demand_uplift_pct=150.0,
            status="ACTIVE"
        )
        db.session.add(event)
        db.session.commit()

        wizard = run_11_step_festival_planning_wizard(event.id, self.user.id)
        self.assertEqual(len(wizard['steps']), 11)
        self.assertGreater(wizard['summary']['expected_revenue'], 0)

        # Execute Clearance
        clearance_res = execute_post_festival_clearance(event.id, self.user.id)
        self.assertEqual(clearance_res['cleared_products_count'], 1)

    def test_price_intelligence(self):
        # Test manual price update
        update_product_price(self.product.id, 3.99, "Markdown", "Near-expiry discount", self.user.id)
        db.session.refresh(self.product)
        self.assertEqual(self.product.active_price, 3.99)
        self.assertEqual(self.product.markdown_price, 3.99)

        # Check Price History record
        history = PriceHistory.query.filter_by(product_id=self.product.id).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.new_price, 3.99)

    def test_scan_barcode_intelligence(self):
        panel = process_scanned_barcode("890123456701", scan_mode="Intelligence")
        self.assertIsNotNone(panel)
        self.assertEqual(panel['identity']['sku'], "DAIRY-MILK-1L")
        self.assertEqual(panel['commercial']['active_price'], 4.50)

    def test_assistant_natural_language_query(self):
        res = process_assistant_natural_language_query("Which products may stock out this week?")
        self.assertEqual(res['intent'], "Stockout Warning")

if __name__ == '__main__':
    unittest.main()
