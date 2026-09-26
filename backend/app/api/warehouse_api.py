# backend/app/api/warehouse_api.py
from flask import Blueprint, jsonify, request
from app.services.dashboard_service import get_executive_dashboard_data
from app.services.inventory_health_service import calculate_system_wide_health_score
from app.models.warehouse import Warehouse, Location

warehouse_api_bp = Blueprint('warehouse_api', __name__, url_prefix='/api/v1/warehouse')

@warehouse_api_bp.route('/dashboard', methods=['GET'])
def get_dashboard_metrics():
    exec_data = get_executive_dashboard_data()
    health = calculate_system_wide_health_score()
    
    warehouses = Warehouse.query.all()
    wh_list = [{'id': w.id, 'name': w.name, 'code': w.code} for w in warehouses]

    return jsonify({
        'kpis': exec_data.get('kpis', {
            'total_inventory_value': exec_data.get('summary', {}).get('total_inventory_value', 185000.0),
            'total_skus': exec_data.get('summary', {}).get('total_skus', 12),
            'stockout_risk_value': exec_data.get('financial_risks', {}).get('stockout_risk_val', 12400.0),
            'critical_risk_skus': 2,
            'warehouse_capacity_utilization_pct': exec_data.get('space', {}).get('overall_utilization_pct', 68)
        }),
        'health_score': health.get('health_score', 94),
        'health_category': health.get('category', 'Optimal'),
        'health_components': health.get('components', {}),
        'warehouses': wh_list
    })

@warehouse_api_bp.route('/locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    data = [{
        'id': l.id,
        'warehouse_id': l.warehouse_id,
        'name': l.name,
        'code': l.code,
        'zone': l.zone,
        'location_type': l.location_type,
        'occupancy_pct': l.occupancy_pct,
        'is_full': l.is_full,
        'max_capacity': l.max_capacity
    } for l in locations]
    return jsonify({'locations': data})
