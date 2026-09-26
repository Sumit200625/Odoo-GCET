# app/models/stock.py
from datetime import datetime
from app.extensions import db

class StockBalance(db.Model):
    __tablename__ = 'stock_balances'
    __table_args__ = (
        db.UniqueConstraint('product_id', 'location_id', name='uix_product_location'),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    quantity = db.Column(db.Float, default=0.0, nullable=False)
    batch_number = db.Column(db.String(50), default='BATCH-2026-001')
    expiry_date = db.Column(db.DateTime, nullable=True)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < datetime.utcnow()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return 999
        delta = self.expiry_date - datetime.utcnow()
        return delta.days

    def __repr__(self):
        return f'<StockBalance Prod:{self.product_id} Loc:{self.location_id} Qty:{self.quantity}>'
