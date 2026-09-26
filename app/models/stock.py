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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StockBalance Prod:{self.product_id} Loc:{self.location_id} Qty:{self.quantity}>'
