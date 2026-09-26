# backend/app/api/simulator_api.py
from flask import Blueprint, jsonify, request
from app.models.product import Product
from app.services.simulator_service import run_what_if_scenario_simulation

simulator_api_bp = Blueprint('simulator_api', __name__, url_prefix='/api/v1/simulator')

@simulator_api_bp.route('/run', methods=['POST'])
def run_simulation():
    payload = request.get_json() or {}
    product_id = payload.get('product_id', 1)
    params = payload.get('params', {})

    try:
        sim_res = run_what_if_scenario_simulation(product_id=product_id, custom_params=params)
        return jsonify({
            'success': True,
            'simulation': sim_res
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
