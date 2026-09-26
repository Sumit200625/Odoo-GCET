# app/models/grocery.py
import json
from datetime import datetime
from app.extensions import db

class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    store_type = db.Column(db.String(50), default='Supermarket') # Supermarket, Hypermarket, Convenience, Dark Store
    address = db.Column(db.String(255), nullable=True)
    manager_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shelf_locations = db.relationship('ShelfLocation', backref='store', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Store {self.name} ({self.code})>'


class ShelfLocation(db.Model):
    __tablename__ = 'shelf_locations'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    aisle = db.Column(db.String(30), nullable=False)        # Aisle 1 (Dairy), Aisle 2 (Produce), Aisle 3 (Snacks)
    shelf_code = db.Column(db.String(30), nullable=False)   # SH-A1-01
    display_section = db.Column(db.String(50), default='Standard Rack') # Eye-Level, Endcap, Checkout Display, Cooler
    max_capacity = db.Column(db.Float, default=50.0)
    current_stock = db.Column(db.Float, default=0.0)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)

    product = db.relationship('Product')

    @property
    def occupancy_pct(self):
        if not self.max_capacity or self.max_capacity <= 0:
            return 100.0
        return min(100.0, round((self.current_stock / self.max_capacity) * 100.0, 1))

    def __repr__(self):
        return f'<ShelfLocation {self.shelf_code} Store:{self.store_id}>'


class FestivalEvent(db.Model):
    __tablename__ = 'festival_events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Diwali, Dussehra, Navratri, Holi, Eid, Christmas, New Year
    code = db.Column(db.String(50), unique=True, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    prep_start_date = db.Column(db.DateTime, nullable=False) # Procurement start deadline
    post_clearance_end_date = db.Column(db.DateTime, nullable=True)
    
    category_focus = db.Column(db.String(255), default='Sweets, Gifting, Grocery Essentials')
    expected_demand_uplift_pct = db.Column(db.Float, default=45.0)
    status = db.Column(db.String(30), default='Upcoming') # Upcoming, Prep_Phase, Active, Post_Clearance, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plans = db.relationship('FestivalProductPlan', backref='festival_event', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<FestivalEvent {self.name} [{self.status}]>'


class FestivalProductPlan(db.Model):
    __tablename__ = 'festival_product_plans'

    id = db.Column(db.Integer, primary_key=True)
    festival_id = db.Column(db.Integer, db.ForeignKey('festival_events.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    
    baseline_daily_demand = db.Column(db.Float, default=10.0)
    forecast_uplift_pct = db.Column(db.Float, default=50.0)
    recommended_procurement_qty = db.Column(db.Float, nullable=False)
    safety_stock_buffer = db.Column(db.Float, default=20.0)
    
    promotion_price = db.Column(db.Float, nullable=True)
    expected_revenue = db.Column(db.Float, default=0.0)
    expected_margin_pct = db.Column(db.Float, default=25.0)
    leftover_risk_pct = db.Column(db.Float, default=10.0)
    
    status = db.Column(db.String(30), default='Planned') # Planned, Approved, Ordered, Stocked, Cleared
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    store = db.relationship('Store')


class PriceHistory(db.Model):
    __tablename__ = 'price_histories'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    price_type = db.Column(db.String(30), default='Standard') # Standard, Festival, Promotion, Markdown, Margin_Protection
    rationale = db.Column(db.String(255), nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    user = db.relationship('User')

    def __repr__(self):
        return f'<PriceHistory SKU:{self.product_id} {self.old_price}->{self.new_price}>'


class POSSale(db.Model):
    __tablename__ = 'pos_sales'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    total_items_count = db.Column(db.Integer, default=1)
    payment_method = db.Column(db.String(30), default='UPI / Card')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship('Store')
    creator = db.relationship('User')
    items = db.relationship('POSSaleItem', backref='pos_sale', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<POSSale {self.receipt_number} Total:${self.total_amount}>'


class POSSaleItem(db.Model):
    __tablename__ = 'pos_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    pos_sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)

    product = db.relationship('Product')


class ReplenishmentTask(db.Model):
    __tablename__ = 'replenishment_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    
    source_area = db.Column(db.String(50), default='Backroom')
    destination_shelf = db.Column(db.String(50), default='Aisle 1 Shelf 2')
    priority = db.Column(db.String(20), default='HIGH') # CRITICAL, HIGH, NORMAL
    status = db.Column(db.String(30), default='Pending') # Pending, Assigned, Completed, Canceled
    assigned_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    store = db.relationship('Store')
    operator = db.relationship('User')

    def __repr__(self):
        return f'<ReplenishmentTask {self.task_code} [{self.status}]>'


class WasteRecord(db.Model):
    __tablename__ = 'waste_records'

    id = db.Column(db.Integer, primary_key=True)
    record_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    batch_number = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0.0)
    total_cost_waste = db.Column(db.Float, nullable=False)
    
    reason = db.Column(db.String(50), default='Expired') # Expired, Damaged, Spoiled, Cold_Chain_Break, Quality_Reject
    action_taken = db.Column(db.String(100), default='Disposed with manager approval')
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    store = db.relationship('Store')
    recorder = db.relationship('User')

    def __repr__(self):
        return f'<WasteRecord {self.record_code} Reason:{self.reason} Cost:${self.total_cost_waste}>'
