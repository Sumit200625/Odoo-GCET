# app/services/alert_engine.py
"""
Intelligent Alert & Notification Engine for StockSense.
- Smart Alert Generation & Deduplication (prevents duplicate spam alerts within 24h window)
- 5 Severity Levels: Critical, High, Medium, Low, Informational
- Alert Lifecycle: Open -> Acknowledged -> In_Progress -> Resolved -> Dismissed
"""

import uuid
from datetime import datetime, timedelta
from app.extensions import db
from app.models.ai_intelligence import Alert
from app.models.product import Product

def create_smart_alert(
    title,
    description,
    alert_type,
    severity='High',
    product_id=None,
    warehouse_id=None,
    supplier_id=None,
    financial_impact=0.0,
    expected_date=None,
    recommended_action=None,
    assigned_user_id=None,
    due_days=3
):
    """
    Creates a smart alert with automatic deduplication check.
    If an open alert of the same type and product exists within 24h, it updates the existing alert instead of spamming duplicates.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = Alert.query.filter(
        Alert.alert_type == alert_type,
        Alert.product_id == product_id,
        Alert.status.in_(['Open', 'Acknowledged', 'In_Progress']),
        Alert.created_at >= cutoff
    ).first()

    if existing:
        existing.description = description
        existing.financial_impact = max(existing.financial_impact, financial_impact)
        existing.updated_at = datetime.utcnow()
        db.session.commit()
        return existing

    code = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    due_date = datetime.utcnow() + timedelta(days=due_days)

    alert = Alert(
        alert_code=code,
        title=title,
        description=description,
        alert_type=alert_type,
        severity=severity,
        product_id=product_id,
        warehouse_id=warehouse_id,
        supplier_id=supplier_id,
        financial_impact=financial_impact,
        expected_date=expected_date,
        recommended_action=recommended_action,
        assigned_user_id=assigned_user_id,
        due_date=due_date,
        status='Open'
    )

    db.session.add(alert)
    db.session.commit()
    return alert

def resolve_alert(alert_id, user_id, resolution_notes):
    """Marks an alert as resolved with audit timestamp and notes."""
    alert = Alert.query.get_or_404(alert_id)
    alert.status = 'Resolved'
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolution_notes
    db.session.commit()
    return alert
