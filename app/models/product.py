# app/models/product.py
from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    plu_code = db.Column(db.String(20), nullable=True)
    brand = db.Column(db.String(80), default='Generic')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    unit = db.Column(db.String(20), default='pcs')
    image_url = db.Column(db.String(255), nullable=True)
    
    # Financial & Price Intelligence
    unit_cost = db.Column(db.Float, default=50.0)
    mrp = db.Column(db.Float, default=100.0)                # Maximum Retail Price
    selling_price = db.Column(db.Float, default=75.0)       # Current active selling price
    promotion_price = db.Column(db.Float, nullable=True)     # Active promotional price
    markdown_price = db.Column(db.Float, nullable=True)      # Near-expiry markdown price
    holding_cost_annual_pct = db.Column(db.Float, default=20.0)
    
    # Supply Chain & Reorder Parameters
    reorder_level = db.Column(db.Float, default=10.0)
    lead_time_days = db.Column(db.Integer, default=5)
    minimum_order_quantity = db.Column(db.Float, default=10.0)
    economic_order_quantity = db.Column(db.Float, default=50.0)
    pack_size = db.Column(db.Integer, default=1)
    
    # Retail Stock Split (Shelf vs Backroom)
    shelf_stock = db.Column(db.Float, default=0.0)
    backroom_stock = db.Column(db.Float, default=0.0)
    shelf_capacity = db.Column(db.Float, default=30.0)
    
    # Classifications & Tags
    abc_class = db.Column(db.String(5), default='B')
    xyz_class = db.Column(db.String(5), default='Y')
    velocity_class = db.Column(db.String(5), default='F')
    lifecycle_status = db.Column(db.String(20), default='Active')
    is_critical = db.Column(db.Boolean, default=False)
    is_expiry_sensitive = db.Column(db.Boolean, default=False)
    is_perishable = db.Column(db.Boolean, default=False)
    freshness_days = db.Column(db.Integer, default=180)
    shelf_life_days = db.Column(db.Integer, nullable=True, default=180)
    
    # Physical & Handling Specs
    weight_kg = db.Column(db.Float, default=1.0)
    volume_m3 = db.Column(db.Float, default=0.01)
    temperature_requirement = db.Column(db.String(20), default='Ambient') # Ambient, Cold, Frozen
    hazard_class = db.Column(db.String(20), default='None')
    is_fragile = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stock_balances = db.relationship('StockBalance', backref='product', lazy=True, cascade='all, delete-orphan')
    inventory_batches = db.relationship('InventoryBatch', backref='product', lazy=True, cascade='all, delete-orphan')

    @property
    def total_stock(self):
        wh_stock = sum(b.quantity for b in self.stock_balances)
        return round(wh_stock + (self.shelf_stock or 0.0) + (self.backroom_stock or 0.0), 2)

    @property
    def warehouse_stock(self):
        return sum(b.quantity for b in self.stock_balances)

    @property
    def total_value(self):
        return round(self.total_stock * (self.unit_cost or 50.0), 2)

    @property
    def active_price(self):
        if self.markdown_price and self.markdown_price > 0:
            return self.markdown_price
        if self.promotion_price and self.promotion_price > 0:
            return self.promotion_price
        return self.selling_price or 75.0

    @property
    def discount_pct(self):
        mrp = self.mrp or self.selling_price or 100.0
        if mrp <= 0:
            return 0.0
        diff = mrp - self.active_price
        return round(max(0.0, (diff / mrp) * 100.0), 1)

    @property
    def margin_pct(self):
        price = self.active_price
        cost = self.unit_cost or 50.0
        if price <= 0:
            return 0.0
        return round(((price - cost) / price) * 100.0, 1)

    @property
    def abc_xyz_matrix(self):
        return f"{self.abc_class or 'B'}{self.xyz_class or 'Y'}"

    @property
    def stock_status(self):
        total = self.total_stock
        if total <= 0:
            return 'Out of Stock'
        elif total <= self.reorder_level:
            return 'Low Stock'
        return 'In Stock'

    def __repr__(self):
        return f'<Product {self.name} ({self.sku}) Barcode:{self.barcode}>'
