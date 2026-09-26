# app/models/warehouse.py
from app.extensions import db

class Warehouse(db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    locations = db.relationship('Location', backref='warehouse', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Warehouse {self.name} ({self.code})>'

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    location_type = db.Column(db.String(50), default='Internal') # Internal, Customer, Vendor, Inventory Loss
    max_capacity = db.Column(db.Float, default=500.0) # Maximum units storage capacity
    zone = db.Column(db.String(50), default='Zone A')  # Zone A, Zone B, Cold Storage, Fast-Pick

    stock_balances = db.relationship('StockBalance', backref='location', lazy=True)

    @property
    def occupied_quantity(self):
        return sum(b.quantity for b in self.stock_balances if b.quantity > 0)

    @property
    def available_capacity(self):
        return max(0.0, (self.max_capacity or 500.0) - self.occupied_quantity)

    @property
    def occupancy_percentage(self):
        max_cap = self.max_capacity or 500.0
        if max_cap <= 0:
            return 100.0
        return min(100.0, round((self.occupied_quantity / max_cap) * 100.0, 1))

    @property
    def full_name(self):
        return f"{self.warehouse.name} / {self.name}"

    def __repr__(self):
        return f'<Location {self.name} ({self.code})>'
