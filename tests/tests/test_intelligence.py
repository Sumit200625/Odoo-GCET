# tests/test_intelligence.py
import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.stock import StockBalance, InventoryBatch
from app.models.supplier import Supplier
from app.services.forecasting_engine import generate_ai_forecast_for_sku
from app.services.predictive_risk_engine import run_predictive_risk_assessment
from app.services.replenishment_engine import (
    calculate_dynamic_safety_stock,
    generate_reorder_recommendation_for_sku,
    approve_reorder_recommendation
)
from app.services.putaway_slotting_engine import recommend_directed_putaway_location
from app.services.picking_outbound_engine import allocate_batches_fefo_or_fifo
from app.services.simulator_service import run_what_if_scenario_simulation

class IntelligenceEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create basic test entities
        self.user = User(name="Test Admin", email="admin@stocksense.com", role="super_admin")
        self.user.set_password("pass")
        db.session.add(self.user)

        self.wh = Warehouse(name="Main Hub", code="WH-HUB-01")
        db.session.add(self.wh)
        db.session.commit()

        self.loc_main = Location(warehouse_id=self.wh.id, name="Main Rack A", code="LOC-A1", location_type="Internal", max_capacity=500.0, zone="Zone A")
        self.loc_cold = Location(warehouse_id=self.wh.id, name="Cold Storage B", code="LOC-B1", location_type="Internal", max_capacity=300.0, temperature_condition="Cold", zone="Zone B")
        db.session.add_all([self.loc_main, self.loc_cold])

        self.cat = Category(name="Electronics")
        db.session.add(self.cat)
        db.session.commit()

        self.product = Product(
            name="ARM Microcontroller", sku="ARM-MC-001", category_id=self.cat.id,
            unit="pcs", unit_cost=100.0, selling_price=150.0, reorder_level=20.0, lead_time_days=5
        )
        db.session.add(self.product)

        self.supplier = Supplier(name="Tech Supply Co", code="SUP-TECH", lead_time_days=5, supplier_score=95.0)
        db.session.add(self.supplier)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_dynamic_safety_stock_calculation(self):
        ss = calculate_dynamic_safety_stock(self.product.id)
        self.assertGreaterEqual(ss, self.product.reorder_level)

    def test_reorder_recommendation_and_approval(self):
        # Stock at 10.0 (below reorder level of 20.0)
        sb = StockBalance(product_id=self.product.id, location_id=self.loc_main.id, quantity=10.0)
        db.session.add(sb)
        db.session.commit()
        db.session.expire_all()

        rec = generate_reorder_recommendation_for_sku(self.product.id, warehouse_id=self.wh.id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.recommended_action, 'Reorder')
        self.assertEqual(rec.approval_status, 'Generated')

        # Approve and generate PO
        po = approve_reorder_recommendation(rec.id, self.user.id)
        self.assertIsNotNone(po)
        self.assertEqual(po.status, 'Approved')
        self.assertEqual(rec.approval_status, 'Executed')

    def test_directed_putaway_recommendation(self):
        recs = recommend_directed_putaway_location(self.product.id, quantity=50.0)
        self.assertGreater(len(recs), 0)
        self.assertEqual(recs[0]['code'], 'LOC-A1')

    def test_fefo_batch_allocation(self):
        now = datetime.utcnow()
        b1 = InventoryBatch(batch_number="B1", product_id=self.product.id, location_id=self.loc_main.id, initial_quantity=30.0, current_quantity=30.0, expiry_date=now + timedelta(days=60))
        b2 = InventoryBatch(batch_number="B2", product_id=self.product.id, location_id=self.loc_main.id, initial_quantity=20.0, current_quantity=20.0, expiry_date=now + timedelta(days=10)) # Earliest expiry
        db.session.add_all([b1, b2])
        db.session.commit()

        alloc_res = allocate_batches_fefo_or_fifo(self.product.id, self.loc_main.id, requested_qty=25.0)
        self.assertTrue(alloc_res['is_fulfilled'])
        self.assertEqual(alloc_res['allocations'][0]['batch_number'], 'B2') # Earliest expiry batch prioritized

    def test_what_if_scenario_simulation(self):
        sim = run_what_if_scenario_simulation(demand_increase_pct=50.0, lead_time_delay_days=3, user_id=self.user.id)
        self.assertIn('summary', sim)
        self.assertEqual(sim['summary']['demand_increase_pct'], 50.0)

if __name__ == '__main__':
    unittest.main()
