# app/routes/adjustments.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.operation import Adjustment, AdjustmentLine
from app.models.warehouse import Location
from app.models.product import Product
from app.services.stock_service import validate_adjustment, get_location_stock
from app.utils.rbac import role_required

adjustments_bp = Blueprint('adjustments', __name__, url_prefix='/adjustments')

@adjustments_bp.route('')
@login_required
def index():
    status = request.args.get('status', '').strip()
    query = Adjustment.query.order_by(Adjustment.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    adjustments = query.all()
    return render_template('adjustments/index.html', adjustments=adjustments, current_status=status)

@adjustments_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def create():
    locations = Location.query.all()
    products = Product.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        location_id = request.form.get('location_id', type=int)
        reason = request.form.get('reason', '').strip()
        product_ids = request.form.getlist('product_id[]')
        counted_quantities = request.form.getlist('counted_quantity[]')

        if not location_id:
            flash('Location is required for inventory adjustment.', 'danger')
            return render_template('adjustments/form.html', locations=locations, products=products)

        if not product_ids or not counted_quantities:
            flash('At least one product line is required.', 'danger')
            return render_template('adjustments/form.html', locations=locations, products=products)

        reference = f"ADJ-{uuid.uuid4().hex[:6].upper()}"

        adjustment = Adjustment(
            reference=reference,
            location_id=location_id,
            reason=reason or "Physical Count Audit",
            status='Draft',
            created_by=current_user.id
        )
        db.session.add(adjustment)
        db.session.flush()

        has_valid_line = False
        for pid_str, counted_str in zip(product_ids, counted_quantities):
            if pid_str and counted_str is not None and counted_str != '':
                try:
                    pid = int(pid_str)
                    counted_qty = float(counted_str)
                    if counted_qty >= 0:
                        recorded_qty = get_location_stock(pid, location_id)
                        diff = counted_qty - recorded_qty

                        line = AdjustmentLine(
                            adjustment_id=adjustment.id,
                            product_id=pid,
                            recorded_quantity=recorded_qty,
                            counted_quantity=counted_qty,
                            difference=diff
                        )
                        db.session.add(line)
                        has_valid_line = True
                except ValueError:
                    continue

        if not has_valid_line:
            db.session.rollback()
            flash('Please specify a valid product and counted quantity.', 'danger')
            return render_template('adjustments/form.html', locations=locations, products=products)

        db.session.commit()
        flash(f'Stock Adjustment "{adjustment.reference}" created in Draft status.', 'success')
        return redirect(url_for('adjustments.view', id=adjustment.id))

    return render_template('adjustments/form.html', locations=locations, products=products)


@adjustments_bp.route('/<int:id>')
@login_required
def view(id):
    adjustment = Adjustment.query.get_or_404(id)
    return render_template('adjustments/view.html', adjustment=adjustment)


@adjustments_bp.route('/<int:id>/validate', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def validate(id):
    try:
        adjustment = validate_adjustment(id, current_user.id)
        flash(f'Adjustment "{adjustment.reference}" validated successfully! Stock updated to physical count.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'An unexpected error occurred during adjustment validation: {str(e)}', 'danger')

    return redirect(url_for('adjustments.view', id=id))


@adjustments_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def cancel(id):
    adjustment = Adjustment.query.get_or_404(id)
    if adjustment.status == 'Done':
        flash('Validated adjustments cannot be canceled.', 'danger')
    else:
        adjustment.status = 'Canceled'
        db.session.commit()
        flash(f'Adjustment "{adjustment.reference}" canceled.', 'info')

    return redirect(url_for('adjustments.view', id=id))


@adjustments_bp.route('/api/get-stock')
@login_required
def api_get_stock():
    product_id = request.args.get('product_id', type=int)
    location_id = request.args.get('location_id', type=int)

    if not product_id or not location_id:
        return jsonify({'recorded_quantity': 0.0})

    stock = get_location_stock(product_id, location_id)
    return jsonify({'recorded_quantity': stock})
