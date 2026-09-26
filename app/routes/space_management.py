# app/routes/space_management.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.warehouse import Warehouse, Location
from app.models.operation import PutawayTask, PickTask, Receipt
from app.services.putaway_slotting_engine import (
    calculate_space_utilization_analytics,
    simulate_slotting_rebalancing,
    confirm_putaway_task_execution,
    generate_putaway_task
)
from app.services.picking_outbound_engine import confirm_pick_task_execution

space_bp = Blueprint('space_management', __name__, url_prefix='/space')

@space_bp.route('/')
@login_required
def index():
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    selected_wh_id = request.args.get('warehouse_id', type=int) or (warehouses[0].id if warehouses else None)
    
    analytics = calculate_space_utilization_analytics(selected_wh_id)
    putaway_tasks = PutawayTask.query.filter_by(status='Pending').all()
    pick_tasks = PickTask.query.filter_by(status='Pending').order_by(PickTask.pick_path_sequence.asc()).all()

    return render_template(
        'space_management/index.html',
        warehouses=warehouses,
        selected_wh_id=selected_wh_id,
        analytics=analytics,
        putaway_tasks=putaway_tasks,
        pick_tasks=pick_tasks
    )

@space_bp.route('/slotting-simulation')
@login_required
def slotting_simulation():
    res = simulate_slotting_rebalancing()
    return render_template('space_management/slotting_simulation.html', simulation=res)

@space_bp.route('/putaway/<int:task_id>/confirm', methods=['POST'])
@login_required
def confirm_putaway(task_id):
    actual_loc_id = request.form.get('actual_location_id', type=int)
    override_reason = request.form.get('override_reason')
    try:
        confirm_putaway_task_execution(task_id, actual_loc_id, current_user.id, override_reason)
        flash("Put-away task confirmed successfully! Inventory updated.", "success")
    except Exception as e:
        flash(f"Put-away confirmation failed: {str(e)}", "danger")
    return redirect(url_for('space_management.index'))

@space_bp.route('/picking/<int:task_id>/confirm', methods=['POST'])
@login_required
def confirm_picking(task_id):
    picked_qty = float(request.form.get('picked_quantity', 0.0))
    short_reason = request.form.get('short_pick_reason')
    try:
        res = confirm_pick_task_execution(task_id, picked_qty, current_user.id, short_reason)
        if res['substitute_info']:
            flash(f"Pick task completed with short-pick. Recommended substitute: {res['substitute_info']['recommended_substitute_name']}", "warning")
        else:
            flash("Pick task completed successfully!", "success")
    except Exception as e:
        flash(f"Pick confirmation failed: {str(e)}", "danger")
    return redirect(url_for('space_management.index'))
