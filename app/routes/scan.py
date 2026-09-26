# app/routes/scan.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.scan_intelligence_service import process_scanned_barcode

scan_bp = Blueprint('scan', __name__, url_prefix='/scan')

@scan_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    scan_query = request.args.get('barcode') or request.form.get('barcode')
    mode = request.args.get('mode', 'Intelligence')
    
    panel_data = None
    if scan_query:
        panel_data = process_scanned_barcode(scan_query, scan_mode=mode)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(panel_data)

    return render_template('scan/index.html', panel=panel_data, scan_query=scan_query, mode=mode)
