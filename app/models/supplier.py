# app/models/supplier.py
from datetime import datetime
from app.extensions import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    contact_email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    
    # Supplier Intelligence KPIs
    lead_time_days = db.Column(db.Integer, default=5)
    lead_time_variance_days = db.Column(db.Float, default=1.0)
    on_time_delivery_rate = db.Column(db.Float, default=95.0)  # 0 to 100%
    fill_rate_pct = db.Column(db.Float, default=98.0)          # 0 to 100%
    quality_acceptance_rate = db.Column(db.Float, default=97.0)# 0 to 100%
    defect_rate_pct = db.Column(db.Float, default=1.5)         # 0 to 100%
    damage_count = db.Column(db.Integer, default=2)
    price_stability_score = db.Column(db.Float, default=95.0)  # 0 to 100%
    minimum_order_quantity = db.Column(db.Float, default=10.0)
    return_rate_pct = db.Column(db.Float, default=1.0)
    response_time_hours = db.Column(db.Float, default=4.0)
    po_discrepancy_rate = db.Column(db.Float, default=2.0)
    
    # Overall Supplier Scorecard & Classification
    supplier_score = db.Column(db.Float, default=92.0) # 0 to 100
    classification = db.Column(db.String(20), default='Reliable') # Strategic, Reliable, Monitor, High Risk, Blocked
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def computed_score(self):
        # Weighted Scorecard Calculation:
        # On-Time Delivery (30%), Quality Acceptance (30%), Fill Rate (20%), Price Stability (10%), Response Time (10%)
        score = (
            (self.on_time_delivery_rate or 90.0) * 0.30 +
            (self.quality_acceptance_rate or 90.0) * 0.30 +
            (self.fill_rate_pct or 90.0) * 0.20 +
            (self.price_stability_score or 90.0) * 0.10 +
            max(0.0, (100.0 - (self.response_time_hours or 4.0) * 2.0)) * 0.10
        )
        return round(min(100.0, max(0.0, score)), 1)

    @property
    def computed_classification(self):
        score = self.computed_score
        if score >= 90.0:
            return 'Strategic'
        elif score >= 80.0:
            return 'Reliable'
        elif score >= 65.0:
            return 'Monitor'
        else:
            return 'High Risk'

    def __repr__(self):
        return f'<Supplier {self.name} ({self.code}) Score:{self.computed_score}>'
