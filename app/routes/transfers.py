# app/routes/transfers.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.operation import Transfer, TransferLine
from app.models.warehouse import Location
from app.models.product import Product
from app.services.stock_service import validate_transfer, get_location_stock
from app.utils.decorators import role_required

transfers_bp = Blueprint('transfers', __name__, url_prefix='/transfers')

@transfers_bp.route('')
@login_required
def index():
    status = request.args.get('status', '').strip()
    query = Transfer.query.order_by(Transfer.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    transfers = query.all()
    return render_template('transfers/index.html', transfers=transfers, current_status=status)

@transfers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    locations = Location.query.all()
    products = Product.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        source_location_id = request.form.get('source_location_id', type=int)
        destination_location_id = request.form.get('destination_location_id', type=int)
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        if not source_location_id or not destination_location_id:
            flash('Source Location and Destination Location are required.', 'danger')
            return render_template('transfers/form.html', locations=locations, products=products)

        if source_location_id == destination_location_id:
            flash('Source and Destination locations must be different.', 'danger')
            return render_template('transfers/form.html', locations=locations, products=products)

        if not product_ids or not quantities:
            flash('At least one product line is required.', 'danger')
            return render_template('transfers/form.html', locations=locations, products=products)

        reference = f"TRN-{uuid.uuid4().hex[:6].upper()}"

        transfer = Transfer(
            reference=reference,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            status='Draft',
            created_by=current_user.id
        )
        db.session.add(transfer)
        db.session.flush()

        has_valid_line = False
        for pid_str, qty_str in zip(product_ids, quantities):
            if pid_str and qty_str:
                try:
                    pid = int(pid_str)
                    qty = float(qty_str)
                    if qty > 0:
                        line = TransferLine(transfer_id=transfer.id, product_id=pid, quantity=qty)
                        db.session.add(line)
                        has_valid_line = True
                except ValueError:
                    continue

        if not has_valid_line:
            db.session.rollback()
            flash('Please specify a valid product and positive quantity.', 'danger')
            return render_template('transfers/form.html', locations=locations, products=products)

        db.session.commit()
        flash(f'Transfer "{transfer.reference}" created in Draft status.', 'success')
        return redirect(url_for('transfers.view', id=transfer.id))

    return render_template('transfers/form.html', locations=locations, products=products)


@transfers_bp.route('/<int:id>')
@login_required
def view(id):
    transfer = Transfer.query.get_or_404(id)
    availability = {}
    for line in transfer.lines:
        avail = get_location_stock(line.product_id, transfer.source_location_id)
        availability[line.id] = {
            'available': avail,
            'sufficient': avail >= line.quantity
        }

    return render_template('transfers/view.html', transfer=transfer, availability=availability)


@transfers_bp.route('/<int:id>/validate', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def validate(id):
    try:
        transfer = validate_transfer(id, current_user.id)
        flash(f'Transfer "{transfer.reference}" validated successfully! Stock moved between locations.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'An unexpected error occurred during transfer validation: {str(e)}', 'danger')

    return redirect(url_for('transfers.view', id=id))


@transfers_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def cancel(id):
    transfer = Transfer.query.get_or_404(id)
    if transfer.status == 'Done':
        flash('Validated transfers cannot be canceled.', 'danger')
    else:
        transfer.status = 'Canceled'
        db.session.commit()
        flash(f'Transfer "{transfer.reference}" canceled.', 'info')

    return redirect(url_for('transfers.view', id=id))
