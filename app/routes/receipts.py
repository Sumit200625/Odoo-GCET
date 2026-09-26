# app/routes/receipts.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.operation import Receipt, ReceiptLine
from app.models.warehouse import Location
from app.models.product import Product
from app.services.stock_service import validate_receipt

receipts_bp = Blueprint('receipts', __name__, url_prefix='/receipts')

@receipts_bp.route('')
@login_required
def index():
    status = request.args.get('status', '').strip()
    query = Receipt.query.order_by(Receipt.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    receipts = query.all()
    return render_template('receipts/index.html', receipts=receipts, current_status=status)

@receipts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    locations = Location.query.all()
    products = Product.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name', '').strip()
        destination_location_id = request.form.get('destination_location_id', type=int)
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        if not supplier_name or not destination_location_id:
            flash('Supplier Name and Destination Location are required.', 'danger')
            return render_template('receipts/form.html', locations=locations, products=products)

        if not product_ids or not quantities:
            flash('At least one product line is required.', 'danger')
            return render_template('receipts/form.html', locations=locations, products=products)

        reference = f"REC-{uuid.uuid4().hex[:6].upper()}"

        receipt = Receipt(
            reference=reference,
            supplier_name=supplier_name,
            destination_location_id=destination_location_id,
            status='Draft',
            created_by=current_user.id
        )
        db.session.add(receipt)
        db.session.flush()

        has_valid_line = False
        for pid_str, qty_str in zip(product_ids, quantities):
            if pid_str and qty_str:
                try:
                    pid = int(pid_str)
                    qty = float(qty_str)
                    if qty > 0:
                        line = ReceiptLine(receipt_id=receipt.id, product_id=pid, quantity=qty)
                        db.session.add(line)
                        has_valid_line = True
                except ValueError:
                    continue

        if not has_valid_line:
            db.session.rollback()
            flash('Please specify a valid product and positive quantity.', 'danger')
            return render_template('receipts/form.html', locations=locations, products=products)

        db.session.commit()
        flash(f'Receipt "{receipt.reference}" created in Draft status.', 'success')
        return redirect(url_for('receipts.view', id=receipt.id))

    return render_template('receipts/form.html', locations=locations, products=products)


@receipts_bp.route('/<int:id>')
@login_required
def view(id):
    receipt = Receipt.query.get_or_404(id)
    return render_template('receipts/view.html', receipt=receipt)


@receipts_bp.route('/<int:id>/validate', methods=['POST'])
@login_required
def validate(id):
    try:
        receipt = validate_receipt(id, current_user.id)
        flash(f'Receipt "{receipt.reference}" validated successfully! Stock updated.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'An unexpected error occurred during receipt validation: {str(e)}', 'danger')

    return redirect(url_for('receipts.view', id=id))


@receipts_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    receipt = Receipt.query.get_or_404(id)
    if receipt.status == 'Done':
        flash('Validated receipts cannot be canceled.', 'danger')
    else:
        receipt.status = 'Canceled'
        db.session.commit()
        flash(f'Receipt "{receipt.reference}" canceled.', 'info')

    return redirect(url_for('receipts.view', id=id))
