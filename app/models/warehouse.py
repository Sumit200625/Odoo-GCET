# app/models/warehouse.py
from datetime import datetime
from app.extensions import db

class Warehouse(db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    total_capacity_m3 = db.Column(db.Float, default=5000.0)
    temperature_control = db.Column(db.String(50), default='Standard Ambient')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    locations = db.relationship('Location', backref='warehouse', lazy=True, cascade='all, delete-orphan')

    @property
    def total_occupied_quantity(self):
        return sum(loc.occupied_quantity for loc in self.locations)

    @property
    def overall_occupancy_pct(self):
        total_cap = sum(loc.max_capacity for loc in self.locations) or 1.0
        return round((self.total_occupied_quantity / total_cap) * 100.0, 1)

    def __repr__(self):
        return f'<Warehouse {self.name} ({self.code})>'

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    location_type = db.Column(db.String(50), default='Internal') # Internal, Customer, Vendor, Quarantine, Staging, Dispatch
    
    # Hierarchy Breakdown
    zone = db.Column(db.String(50), default='Zone A')    # Zone A, Zone B, Cold Storage, Receiving, Dispatch
    aisle = db.Column(db.String(20), default='Ais-1')   # Aisle identifier
    rack = db.Column(db.String(20), default='Rk-01')    # Rack identifier
    shelf = db.Column(db.String(20), default='Sh-1')    # Shelf identifier
    bin_code = db.Column(db.String(20), default='Bn-01')# Bin identifier
    
    # Capacity & Physical Limits
    max_capacity = db.Column(db.Float, default=500.0)    # Unit volume capacity
    max_weight_kg = db.Column(db.Float, default=2000.0)  # Max weight capacity
    current_weight_kg = db.Column(db.Float, default=0.0) # Current stored weight
    reserved_capacity = db.Column(db.Float, default=0.0) # Capacity held for pending putaways
    
    # Environmental & Handling Specs
    allowed_category = db.Column(db.String(100), default='All')
    temperature_condition = db.Column(db.String(20), default='Ambient') # Ambient, Cold, Frozen
    hazard_restriction = db.Column(db.String(20), default='None')
    picking_frequency = db.Column(db.String(20), default='Medium')      # High (Fast-Pick), Medium, Low
    distance_to_dispatch_m = db.Column(db.Float, default=25.0)           # Distance to dispatch bay in meters
    picking_height_level = db.Column(db.Integer, default=1)             # 1 (Floor level), 2 (Mid height), 3 (High level)
    
    # Status
    status = db.Column(db.String(20), default='Available') # Available, Occupied, Full, Blocked, Maintenance, Quarantine

    stock_balances = db.relationship('StockBalance', backref='location', lazy=True)

    @property
    def occupied_quantity(self):
        return sum(b.quantity for b in self.stock_balances if b.quantity > 0)

    @property
    def available_capacity(self):
        return max(0.0, (self.max_capacity or 500.0) - self.occupied_quantity - self.reserved_capacity)

    @property
    def occupancy_percentage(self):
        max_cap = self.max_capacity or 500.0
        if max_cap <= 0:
            return 100.0
        return min(100.0, round(((self.occupied_quantity + self.reserved_capacity) / max_cap) * 100.0, 1))

    @property
    def full_name(self):
        wh_name = self.warehouse.name if self.warehouse else "WH"
        return f"{wh_name} / {self.zone} / {self.code}"

    def __repr__(self):
        return f'<Location {self.name} ({self.code})>'
