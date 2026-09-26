# app/routes/alerts.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.ai_intelligence import Alert
from app.services.alert_engine import resolve_alert

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')

@alerts_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'Open')
    query = Alert.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    return render_template('alerts/index.html', alerts=alerts, status_filter=status_filter)

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve(alert_id):
    notes = request.form.get('notes', 'Resolved by user action')
    try:
        resolve_alert(alert_id, current_user.id, notes)
        flash("Alert resolved successfully.", "success")
    except Exception as e:
        flash(f"Resolution failed: {str(e)}", "danger")
    return redirect(url_for('alerts.index'))
