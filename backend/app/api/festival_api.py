# backend/app/api/festival_api.py
from flask import Blueprint, jsonify, request
from app.services.festival_planning_service import (
    get_active_and_upcoming_festivals,
    run_11_step_festival_planning_wizard,
    execute_post_festival_clearance
)

festival_api_bp = Blueprint('festival_api', __name__, url_prefix='/api/v1/festivals')

@festival_api_bp.route('/', methods=['GET'])
def get_festivals():
    events = get_active_and_upcoming_festivals()
    event_list = [{
        'id': ev.id,
        'name': ev.name,
        'code': ev.code,
        'start_date': ev.start_date.strftime('%Y-%m-%d'),
        'end_date': ev.end_date.strftime('%Y-%m-%d'),
        'status': ev.status,
        'expected_demand_uplift_pct': ev.expected_demand_uplift_pct
    } for ev in events]

    selected_event_id = request.args.get('event_id', type=int) or (events[0].id if events else None)
    wizard = None
    if selected_event_id:
        wizard = run_11_step_festival_planning_wizard(selected_event_id)

    return jsonify({
        'events': event_list,
        'selected_event_id': selected_event_id,
        'wizard': wizard
    })

@festival_api_bp.route('/<int:festival_id>/clearance', methods=['POST'])
def execute_clearance(festival_id):
    try:
        res = execute_post_festival_clearance(festival_id)
        return jsonify({
            'success': True,
            'result': res,
            'message': f"Post-Event Clearance executed for '{res['event_name']}'. 30% markdown applied to {res['cleared_products_count']} leftover SKUs."
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
