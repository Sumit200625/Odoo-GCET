# app/models/product.py
from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    unit = db.Column(db.String(20), default='pcs')
    unit_cost = db.Column(db.Float, default=50.0)
    reorder_level = db.Column(db.Float, default=10.0)
    lead_time_days = db.Column(db.Integer, default=5)
    abc_class = db.Column(db.String(5), default='B') # A, B, C
    fsn_class = db.Column(db.String(5), default='F') # F (Fast), S (Slow), N (Non-moving)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stock_balances = db.relationship('StockBalance', backref='product', lazy=True, cascade='all, delete-orphan')

    @property
    def total_stock(self):
        return sum(b.quantity for b in self.stock_balances)

    @property
    def total_value(self):
        return round(self.total_stock * (self.unit_cost or 50.0), 2)

    @property
    def stock_status(self):
        total = self.total_stock
        if total <= 0:
            return 'Out of Stock'
        elif total <= self.reorder_level:
            return 'Low Stock'
        return 'In Stock'

    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'
