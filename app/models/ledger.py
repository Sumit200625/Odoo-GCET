# app/models/ledger.py
from datetime import datetime
from app.extensions import db

class StockLedger(db.Model):
    __tablename__ = 'stock_ledger'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    operation_type = db.Column(db.String(30), nullable=False) # Receipt, Delivery, Transfer, Adjustment
    reference = db.Column(db.String(50), nullable=False)
    quantity_change = db.Column(db.Float, nullable=False)
    quantity_before = db.Column(db.Float, nullable=False)
    quantity_after = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    location = db.relationship('Location')
    creator = db.relationship('User')

    def __repr__(self):
        return f'<StockLedger {self.operation_type} Ref:{self.reference} Change:{self.quantity_change}>'
