# app/services/audit_approval_service.py
"""
Audit Log & Human Approval Workflow Service for StockSense.
Tracks decisions across the approval lifecycle:
Generated -> Reviewed -> Approved/Rejected -> Executed -> Verified
Persists permanent immutable AuditLogs for compliance and AI learning feedback.
"""

from datetime import datetime
from app.extensions import db
from app.models.ai_intelligence import AuditLog, ReorderRecommendation
from app.models.user import User

def record_audit_entry(action_type, entity_name, entity_id, description, user_id, previous_state=None, new_state=None):
    """Creates an immutable audit log record."""
    entry = AuditLog(
        action_type=action_type,
        entity_name=entity_name,
        entity_id=str(entity_id),
        description=description,
        previous_state=str(previous_state) if previous_state else None,
        new_state=str(new_state) if new_state else None,
        performed_by=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    return entry

def reject_recommendation_with_reason(rec_id, user_id, rejection_reason):
    """
    Records a user rejection of an AI recommendation with the user's explicit reason.
    Feedback is stored in AuditLog to enable continuous recommendation tuning.
    """
    rec = ReorderRecommendation.query.get_or_404(rec_id)
    rec.approval_status = 'Rejected'
    rec.rejection_reason = rejection_reason
    rec.approved_by_id = user_id

    record_audit_entry(
        action_type="Reject_Recommendation",
        entity_name="ReorderRecommendation",
        entity_id=rec.rec_code,
        description=f"User rejected recommendation for {rec.product.name} ({rec.product.sku}). Reason: {rejection_reason}",
        user_id=user_id,
        previous_state="Generated",
        new_state="Rejected"
    )

    db.session.commit()
    return rec
