# app/routes/dashboard.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.dashboard_service import get_dashboard_kpis, get_recent_movements, get_low_stock_alerts
from app.models.warehouse import Warehouse
from app.models.product import Category
from app.utils.decorators import role_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    selected_wh = request.args.get('warehouse_id', type=int)
    
    kpis = get_dashboard_kpis(warehouse_id=selected_wh)
    recent_movements = get_recent_movements(limit=8)
    low_stock_alerts = get_low_stock_alerts()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    categories = Category.query.all()

    return render_template(
        'dashboard/index.html',
        kpis=kpis,
        recent_movements=recent_movements,
        low_stock_alerts=low_stock_alerts,
        warehouses=warehouses,
        categories=categories,
        selected_wh=selected_wh
    )

@dashboard_bp.route('/settings')
@login_required
@role_required('admin', 'manager')
def settings():
    return render_template('dashboard/settings.html')
