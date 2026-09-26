# app/routes/domain.py
from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
from app.services.inventory_health_service import calculate_system_wide_health_score
from app.services.grocery_intelligence_service import get_grocery_dashboard_data
from app.services.dashboard_service import get_warehouse_manager_dashboard_data

domain_bp = Blueprint('domain', __name__)

@domain_bp.route('/domain-select')
@login_required
def select():
    system_health = calculate_system_wide_health_score()
    grocery_data = get_grocery_dashboard_data()
    warehouse_data = get_warehouse_manager_dashboard_data()

    return render_template(
        'domain/select.html',
        system_health=system_health,
        grocery_data=grocery_data,
        warehouse_data=warehouse_data
    )

@domain_bp.route('/switch-domain/<domain_name>')
@login_required
def switch_domain(domain_name):
    if domain_name not in ['warehouse', 'grocery']:
        domain_name = 'warehouse'

    session['active_domain'] = domain_name
    if domain_name == 'grocery':
        return redirect(url_for('grocery.dashboard'))
    else:
        return redirect(url_for('dashboard.index'))
