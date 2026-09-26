# app/routes/festivals.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.festival_planning_service import (
    get_active_and_upcoming_festivals,
    run_11_step_festival_planning_wizard,
    execute_post_festival_clearance
)

festivals_bp = Blueprint('festivals', __name__, url_prefix='/festivals')

@festivals_bp.route('/')
@login_required
def index():
    events = get_active_and_upcoming_festivals()
    selected_event_id = request.args.get('event_id', type=int) or (events[0].id if events else None)
    
    wizard_res = None
    if selected_event_id:
        wizard_res = run_11_step_festival_planning_wizard(selected_event_id, user_id=current_user.id)

    return render_template(
        'festivals/index.html',
        events=events,
        selected_event_id=selected_event_id,
        wizard=wizard_res
    )

@festivals_bp.route('/<int:festival_id>/clearance', methods=['POST'])
@login_required
def clearance(festival_id):
    try:
        res = execute_post_festival_clearance(festival_id, current_user.id)
        flash(f"Post-Event Clearance executed for '{res['event_name']}'. Applied 30% markdown to {res['cleared_products_count']} leftover SKUs.", "info")
    except Exception as e:
        flash(f"Clearance failed: {str(e)}", "danger")
    return redirect(url_for('festivals.index'))
