# app/routes/deliveries.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.operation import Delivery, DeliveryLine
from app.models.warehouse import Location
from app.models.product import Product
from app.services.stock_service import validate_delivery, get_location_stock
from app.utils.decorators import role_required

deliveries_bp = Blueprint('deliveries', __name__, url_prefix='/deliveries')

@deliveries_bp.route('')
@login_required
def index():
    status = request.args.get('status', '').strip()
    query = Delivery.query.order_by(Delivery.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    deliveries = query.all()
    return render_template('deliveries/index.html', deliveries=deliveries, current_status=status)

@deliveries_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    locations = Location.query.all()
    products = Product.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        source_location_id = request.form.get('source_location_id', type=int)
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        if not customer_name or not source_location_id:
            flash('Customer Name and Source Location are required.', 'danger')
            return render_template('deliveries/form.html', locations=locations, products=products)

        if not product_ids or not quantities:
            flash('At least one product line is required.', 'danger')
            return render_template('deliveries/form.html', locations=locations, products=products)

        reference = f"DEL-{uuid.uuid4().hex[:6].upper()}"

        delivery = Delivery(
            reference=reference,
            customer_name=customer_name,
            source_location_id=source_location_id,
            status='Draft',
            created_by=current_user.id
        )
        db.session.add(delivery)
        db.session.flush()

        has_valid_line = False
        for pid_str, qty_str in zip(product_ids, quantities):
            if pid_str and qty_str:
                try:
                    pid = int(pid_str)
                    qty = float(qty_str)
                    if qty > 0:
                        line = DeliveryLine(delivery_id=delivery.id, product_id=pid, quantity=qty)
                        db.session.add(line)
                        has_valid_line = True
                except ValueError:
                    continue

        if not has_valid_line:
            db.session.rollback()
            flash('Please specify a valid product and positive quantity.', 'danger')
            return render_template('deliveries/form.html', locations=locations, products=products)

        db.session.commit()
        flash(f'Delivery order "{delivery.reference}" created in Draft status.', 'success')
        return redirect(url_for('deliveries.view', id=delivery.id))

    return render_template('deliveries/form.html', locations=locations, products=products)


@deliveries_bp.route('/<int:id>')
@login_required
def view(id):
    delivery = Delivery.query.get_or_404(id)
    availability = {}
    for line in delivery.lines:
        avail = get_location_stock(line.product_id, delivery.source_location_id)
        availability[line.id] = {
            'available': avail,
            'sufficient': avail >= line.quantity
        }

    return render_template('deliveries/view.html', delivery=delivery, availability=availability)


@deliveries_bp.route('/<int:id>/validate', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def validate(id):
    try:
        delivery = validate_delivery(id, current_user.id)
        flash(f'Delivery order "{delivery.reference}" validated successfully! Stock deducted.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'An unexpected error occurred during delivery validation: {str(e)}', 'danger')

    return redirect(url_for('deliveries.view', id=id))


@deliveries_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def cancel(id):
    delivery = Delivery.query.get_or_404(id)
    if delivery.status == 'Done':
        flash('Validated deliveries cannot be canceled.', 'danger')
    else:
        delivery.status = 'Canceled'
        db.session.commit()
        flash(f'Delivery order "{delivery.reference}" canceled.', 'info')

    return redirect(url_for('deliveries.view', id=id))
