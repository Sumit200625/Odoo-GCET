# tests/test_stock.py
import unittest
from app import create_app, db
from app.models.user import User
from app.models.warehouse import Warehouse, Location
from app.models.product import Category, Product
from app.models.stock import StockBalance
from app.models.operation import Receipt, ReceiptLine, Delivery, DeliveryLine, Transfer, TransferLine, Adjustment, AdjustmentLine
from app.services.stock_service import validate_receipt, validate_delivery, validate_transfer, validate_adjustment, get_location_stock

class StockSenseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create basic test entities
        self.user = User(name="Tester", email="test@stocksense.com", role="admin")
        self.user.set_password("pass")
        db.session.add(self.user)

        self.wh = Warehouse(name="Test Warehouse", code="WH-TEST")
        db.session.add(self.wh)
        db.session.commit()

        self.loc_a = Location(warehouse_id=self.wh.id, name="Location A", code="LOC-A")
        self.loc_b = Location(warehouse_id=self.wh.id, name="Location B", code="LOC-B")
        db.session.add_all([self.loc_a, self.loc_b])

        self.cat = Category(name="Test Category")
        db.session.add(self.cat)
        db.session.commit()

        self.product = Product(name="Test Steel Rods", sku="TST-STEEL-01", category_id=self.cat.id, unit="kg", reorder_level=10.0)
        db.session.add(self.product)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_receipt_validation(self):
        rec = Receipt(reference="REC-TST-1", supplier_name="Supplier A", destination_location_id=self.loc_a.id, created_by=self.user.id)
        db.session.add(rec)
        db.session.flush()
        line = ReceiptLine(receipt_id=rec.id, product_id=self.product.id, quantity=50.0)
        db.session.add(line)
        db.session.commit()

        validate_receipt(rec.id, self.user.id)

        stock = get_location_stock(self.product.id, self.loc_a.id)
        self.assertEqual(stock, 50.0)
        self.assertEqual(rec.status, "Done")

    def test_delivery_validation_success_and_insufficient_stock(self):
        # Setup initial stock 50.0
        sb = StockBalance(product_id=self.product.id, location_id=self.loc_a.id, quantity=50.0)
        db.session.add(sb)
        db.session.commit()

        # Test delivery exceeding stock (60.0)
        del_fail = Delivery(reference="DEL-FAIL", customer_name="Customer X", source_location_id=self.loc_a.id, created_by=self.user.id)
        db.session.add(del_fail)
        db.session.flush()
        db.session.add(DeliveryLine(delivery_id=del_fail.id, product_id=self.product.id, quantity=60.0))
        db.session.commit()

        with self.assertRaises(ValueError):
            validate_delivery(del_fail.id, self.user.id)

        # Test valid delivery (20.0)
        del_pass = Delivery(reference="DEL-PASS", customer_name="Customer Y", source_location_id=self.loc_a.id, created_by=self.user.id)
        db.session.add(del_pass)
        db.session.flush()
        db.session.add(DeliveryLine(delivery_id=del_pass.id, product_id=self.product.id, quantity=20.0))
        db.session.commit()

        validate_delivery(del_pass.id, self.user.id)
        self.assertEqual(get_location_stock(self.product.id, self.loc_a.id), 30.0)

    def test_internal_transfer(self):
        sb = StockBalance(product_id=self.product.id, location_id=self.loc_a.id, quantity=40.0)
        db.session.add(sb)
        db.session.commit()

        trn = Transfer(reference="TRN-TST", source_location_id=self.loc_a.id, destination_location_id=self.loc_b.id, created_by=self.user.id)
        db.session.add(trn)
        db.session.flush()
        db.session.add(TransferLine(transfer_id=trn.id, product_id=self.product.id, quantity=15.0))
        db.session.commit()

        validate_transfer(trn.id, self.user.id)

        self.assertEqual(get_location_stock(self.product.id, self.loc_a.id), 25.0)
        self.assertEqual(get_location_stock(self.product.id, self.loc_b.id), 15.0)

    def test_stock_adjustment(self):
        sb = StockBalance(product_id=self.product.id, location_id=self.loc_a.id, quantity=100.0)
        db.session.add(sb)
        db.session.commit()

        adj = Adjustment(reference="ADJ-TST", location_id=self.loc_a.id, reason="Damage", created_by=self.user.id)
        db.session.add(adj)
        db.session.flush()
        db.session.add(AdjustmentLine(adjustment_id=adj.id, product_id=self.product.id, recorded_quantity=100.0, counted_quantity=97.0, difference=-3.0))
        db.session.commit()

        validate_adjustment(adj.id, self.user.id)

        self.assertEqual(get_location_stock(self.product.id, self.loc_a.id), 97.0)

if __name__ == '__main__':
    unittest.main()
