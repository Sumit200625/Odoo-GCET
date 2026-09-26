# app/models/operation.py
from datetime import datetime
from app.extensions import db

class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    status = db.Column(db.String(20), default='Draft') # Draft, Waiting, Done, Canceled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    destination_location = db.relationship('Location', foreign_keys=[destination_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('ReceiptLine', backref='receipt', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Receipt {self.reference} [{self.status}]>'

class ReceiptLine(db.Model):
    __tablename__ = 'receipt_lines'

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')


class Delivery(db.Model):
    __tablename__ = 'deliveries'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    status = db.Column(db.String(20), default='Draft') # Draft, Ready, Done, Canceled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('DeliveryLine', backref='delivery', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Delivery {self.reference} [{self.status}]>'

class DeliveryLine(db.Model):
    __tablename__ = 'delivery_lines'

    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey('deliveries.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')


class Transfer(db.Model):
    __tablename__ = 'transfers'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    status = db.Column(db.String(20), default='Draft') # Draft, Waiting, Done, Canceled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    destination_location = db.relationship('Location', foreign_keys=[destination_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('TransferLine', backref='transfer', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Transfer {self.reference} [{self.status}]>'

class TransferLine(db.Model):
    __tablename__ = 'transfer_lines'

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('transfers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')


class Adjustment(db.Model):
    __tablename__ = 'adjustments'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Draft') # Draft, Done, Canceled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    location = db.relationship('Location', foreign_keys=[location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('AdjustmentLine', backref='adjustment', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Adjustment {self.reference} [{self.status}]>'

class AdjustmentLine(db.Model):
    __tablename__ = 'adjustment_lines'

    id = db.Column(db.Integer, primary_key=True)
    adjustment_id = db.Column(db.Integer, db.ForeignKey('adjustments.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    recorded_quantity = db.Column(db.Float, nullable=False)
    counted_quantity = db.Column(db.Float, nullable=False)
    difference = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')
