# app/models/stock.py
from datetime import datetime
from app.extensions import db

class InventoryBatch(db.Model):
    __tablename__ = 'inventory_batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    initial_quantity = db.Column(db.Float, default=0.0)
    current_quantity = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float, default=0.0)
    
    manufacturing_date = db.Column(db.DateTime, nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status: Passed, Quarantine, Damaged, Expired, Hold
    quality_status = db.Column(db.String(30), default='Passed')
    quarantine_reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    location = db.relationship('Location', foreign_keys=[location_id])
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id])

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
        return f'<InventoryBatch {self.batch_number} Prod:{self.product_id} Qty:{self.current_quantity}>'


class StockBalance(db.Model):
    __tablename__ = 'stock_balances'
    __table_args__ = (
        db.UniqueConstraint('product_id', 'location_id', name='uix_product_location'),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    quantity = db.Column(db.Float, default=0.0, nullable=False)            # Total Physical On-Hand Stock
    reserved_quantity = db.Column(db.Float, default=0.0, nullable=False)   # Quantity allocated to outbound orders
    damaged_quantity = db.Column(db.Float, default=0.0, nullable=False)    # Damaged/Unusable stock
    quarantined_quantity = db.Column(db.Float, default=0.0, nullable=False)# Stock held for quality inspection
    in_transit_quantity = db.Column(db.Float, default=0.0, nullable=False)  # Stock currently being transferred
    
    batch_number = db.Column(db.String(50), default='BATCH-2026-001')
    expiry_date = db.Column(db.DateTime, nullable=True)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def available_quantity(self):
        return max(0.0, self.quantity - self.reserved_quantity - self.damaged_quantity - self.quarantined_quantity)

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
        return f'<StockBalance Prod:{self.product_id} Loc:{self.location_id} Total:{self.quantity} Avail:{self.available_quantity}>'


class StockReservation(db.Model):
    __tablename__ = 'stock_reservations'

    id = db.Column(db.Integer, primary_key=True)
    order_reference = db.Column(db.String(50), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    reserved_quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Released, Fulfilled, Expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    location = db.relationship('Location')

    def __repr__(self):
        return f'<StockReservation Ref:{self.order_reference} Qty:{self.reserved_quantity}>'
