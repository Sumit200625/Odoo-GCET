# app/routes/products.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product, Category
from app.models.warehouse import Location
from app.models.stock import StockBalance
from app.models.ledger import StockLedger
from app.utils.rbac import role_required

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    stock_status = request.args.get('stock_status', '').strip()

    query = Product.query.filter_by(is_active=True)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Product.name.ilike(search_pattern)) | (Product.sku.ilike(search_pattern)))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.name).all()

    if stock_status:
        if stock_status == 'out':
            products = [p for p in products if p.total_stock <= 0]
        elif stock_status == 'low':
            products = [p for p in products if 0 < p.total_stock <= p.reorder_level]
        elif stock_status == 'in_stock':
            products = [p for p in products if p.total_stock > p.reorder_level]

    categories = Category.query.all()
    return render_template('products/index.html', products=products, categories=categories, search=search, category_id=category_id, stock_status=stock_status)


@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def create():
    categories = Category.query.all()
    locations = Location.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        category_id = request.form.get('category_id', type=int)
        unit = request.form.get('unit', 'pcs').strip()
        reorder_level = request.form.get('reorder_level', type=float, default=10.0)
        initial_location_id = request.form.get('initial_location_id', type=int)
        initial_stock = request.form.get('initial_stock', type=float, default=0.0)

        if not name or not sku or not category_id:
            flash('Product Name, SKU, and Category are required.', 'danger')
            return render_template('products/form.html', categories=categories, locations=locations, product=None)

        existing_sku = Product.query.filter_by(sku=sku).first()
        if existing_sku:
            flash(f'SKU "{sku}" is already in use by another product.', 'danger')
            return render_template('products/form.html', categories=categories, locations=locations, product=None)

        product = Product(
            name=name,
            sku=sku,
            category_id=category_id,
            unit=unit,
            reorder_level=reorder_level
        )
        db.session.add(product)
        db.session.flush()

        if initial_location_id and initial_stock > 0:
            balance = StockBalance(
                product_id=product.id,
                location_id=initial_location_id,
                quantity=initial_stock
            )
            db.session.add(balance)

            ledger_entry = StockLedger(
                product_id=product.id,
                location_id=initial_location_id,
                operation_type='Receipt',
                reference='INIT-STOCK',
                quantity_change=initial_stock,
                quantity_before=0.0,
                quantity_after=initial_stock,
                reason='Initial Stock Setup',
                created_by=current_user.id
            )
            db.session.add(ledger_entry)

        db.session.commit()
        flash(f'Product "{product.name}" created successfully!', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/form.html', categories=categories, locations=locations, product=None)


@products_bp.route('/<int:id>')
@login_required
def detail(id):
    product = Product.query.get_or_404(id)
    balances = StockBalance.query.filter_by(product_id=product.id).all()
    ledger_history = StockLedger.query.filter_by(product_id=product.id).order_by(StockLedger.created_at.desc()).all()

    return render_template('products/detail.html', product=product, balances=balances, ledger_history=ledger_history)


@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        category_id = request.form.get('category_id', type=int)
        unit = request.form.get('unit', 'pcs').strip()
        reorder_level = request.form.get('reorder_level', type=float, default=10.0)

        if not name or not sku or not category_id:
            flash('Product Name, SKU, and Category are required.', 'danger')
            return render_template('products/form.html', categories=categories, product=product)

        existing_sku = Product.query.filter(Product.sku == sku, Product.id != product.id).first()
        if existing_sku:
            flash(f'SKU "{sku}" is already in use by another product.', 'danger')
            return render_template('products/form.html', categories=categories, product=product)

        product.name = name
        product.sku = sku
        product.category_id = category_id
        product.unit = unit
        product.reorder_level = reorder_level

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully.', 'success')
        return redirect(url_for('products.detail', id=product.id))

    return render_template('products/form.html', categories=categories, product=product)
