# app/models/supplier.py
from datetime import datetime
from app.extensions import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    contact_email = db.Column(db.String(120), nullable=True)
    lead_time_days = db.Column(db.Integer, default=5)
    reliability_score = db.Column(db.Float, default=95.0) # 0 to 100%
    on_time_rate = db.Column(db.Float, default=92.0)      # 0 to 100%
    price_stability_score = db.Column(db.Float, default=98.0) # 0 to 100%
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Supplier {self.name} ({self.code})>'
