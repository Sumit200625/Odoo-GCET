# app/routes/dashboard.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.dashboard_service import (
    get_executive_dashboard_data,
    get_inventory_manager_dashboard_data,
    get_warehouse_manager_dashboard_data,
    get_supplier_portal_dashboard_data,
    get_operations_dashboard_data
)
from app.models.warehouse import Warehouse

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    view_role = request.args.get('role', current_user.role)
    warehouses = Warehouse.query.filter_by(is_active=True).all()

    if view_role in ['super_admin', 'admin', 'executive', 'analyst']:
        data = get_executive_dashboard_data()
        template_name = 'dashboard/executive.html'
    elif view_role in ['inventory_manager', 'manager']:
        data = get_inventory_manager_dashboard_data()
        template_name = 'dashboard/inventory_manager.html'
    elif view_role in ['warehouse_manager', 'warehouse_operator', 'staff']:
        data = get_warehouse_manager_dashboard_data()
        template_name = 'dashboard/warehouse_manager.html'
    elif view_role in ['supplier']:
        data = get_supplier_portal_dashboard_data()
        template_name = 'dashboard/supplier_dashboard.html'
    else:
        data = get_operations_dashboard_data()
        template_name = 'dashboard/operations.html'

    return render_template(
        template_name,
        data=data,
        view_role=view_role,
        warehouses=warehouses
    )
