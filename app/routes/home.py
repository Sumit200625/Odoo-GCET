# app/routes/home.py
import os
from flask import Blueprint, render_template, send_from_directory
from app.models.product import Product
from app.services.scan_intelligence_service import process_scanned_barcode

home_bp = Blueprint('home', __name__)

@home_bp.route('/landing')
@home_bp.route('/')
def landing():
    # Fetch sample product for live interactive homepage demo
    sample_product = Product.query.filter_by(is_active=True).first()
    demo_panel = None
    if sample_product:
        demo_panel = process_scanned_barcode(sample_product.sku)

    return render_template('home/landing.html', demo_panel=demo_panel, sample_product=sample_product)

@home_bp.route('/spa')
def spa_entry():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
    return send_from_directory(frontend_dir, 'index.html')

@home_bp.route('/css/<path:filename>')
def serve_frontend_css(filename):
    css_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'css'))
    return send_from_directory(css_dir, filename)

@home_bp.route('/js/<path:filename>')
def serve_frontend_js(filename):
    js_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'js'))
    return send_from_directory(js_dir, filename)

