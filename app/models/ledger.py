# app/models/ledger.py
import uuid
from datetime import datetime
from app.extensions import db

class StockLedger(db.Model):
    __tablename__ = 'stock_ledger'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: f"TXN-{uuid.uuid4().hex[:10].upper()}")
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    
    # Backwards compatibility helper field
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    
    # Supported transaction types:
    # Purchase receipt, Sale dispatch, Stock transfer, Return, Damage, Expiry,
    # Adjustment, Cycle-count correction, Put-away, Picking, Replenishment, Reservation release
    operation_type = db.Column(db.String(40), nullable=False)
    
    reference = db.Column(db.String(50), nullable=False)
    quantity_change = db.Column(db.Float, nullable=False)
    quantity_before = db.Column(db.Float, nullable=False, default=0.0)
    quantity_after = db.Column(db.Float, nullable=False, default=0.0)
    
    unit_cost = db.Column(db.Float, default=0.0)
    total_value_change = db.Column(db.Float, default=0.0)
    
    reason = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    destination_location = db.relationship('Location', foreign_keys=[destination_location_id])
    location = db.relationship('Location', foreign_keys=[location_id])
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<StockLedger Txn:{self.transaction_id} Type:{self.operation_type} Ref:{self.reference} Change:{self.quantity_change}>'
