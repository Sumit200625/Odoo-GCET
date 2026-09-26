# app/routes/warehouses.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.warehouse import Warehouse, Location
from app.utils.rbac import role_required

warehouses_bp = Blueprint('warehouses', __name__, url_prefix='/warehouses')

@warehouses_bp.route('')
@login_required
def index():
    warehouses = Warehouse.query.all()
    return render_template('warehouses/index.html', warehouses=warehouses)

@warehouses_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_warehouse():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        address = request.form.get('address', '').strip()

        if not name or not code:
            flash('Warehouse Name and Code are required.', 'danger')
            return render_template('warehouses/form.html')

        existing = Warehouse.query.filter_by(code=code).first()
        if existing:
            flash(f'Warehouse Code "{code}" is already taken.', 'danger')
            return render_template('warehouses/form.html')

        warehouse = Warehouse(name=name, code=code, address=address)
        db.session.add(warehouse)
        db.session.commit()

        flash(f'Warehouse "{warehouse.name}" created successfully.', 'success')
        return redirect(url_for('warehouses.index'))

    return render_template('warehouses/form.html')

@warehouses_bp.route('/locations/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def create_location():
    warehouses = Warehouse.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        warehouse_id = request.form.get('warehouse_id', type=int)
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        location_type = request.form.get('location_type', 'Internal')

        if not warehouse_id or not name or not code:
            flash('Warehouse, Location Name, and Code are required.', 'danger')
            return render_template('warehouses/location_form.html', warehouses=warehouses)

        existing = Location.query.filter_by(code=code).first()
        if existing:
            flash(f'Location Code "{code}" is already taken.', 'danger')
            return render_template('warehouses/location_form.html', warehouses=warehouses)

        location = Location(
            warehouse_id=warehouse_id,
            name=name,
            code=code,
            location_type=location_type
        )
        db.session.add(location)
        db.session.commit()

        flash(f'Location "{location.name}" created successfully.', 'success')
        return redirect(url_for('warehouses.index'))

    return render_template('warehouses/location_form.html', warehouses=warehouses)
