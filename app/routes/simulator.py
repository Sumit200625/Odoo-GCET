# app/routes/simulator.py
from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app.services.simulator_service import run_what_if_scenario_simulation

simulator_bp = Blueprint('simulator', __name__, url_prefix='/simulator')

@simulator_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    demand_pct = float(request.form.get('demand_increase_pct', 0.0))
    lead_delay = int(request.form.get('lead_time_delay_days', 0))
    ss_mult = float(request.form.get('safety_stock_multiplier', 1.0))

    simulation_results = run_what_if_scenario_simulation(
        demand_increase_pct=demand_pct,
        lead_time_delay_days=lead_delay,
        safety_stock_multiplier=ss_mult,
        user_id=current_user.id
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(simulation_results)

    return render_template('simulator/index.html', simulation=simulation_results)
