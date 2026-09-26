# backend/app/api/scan_api.py
from flask import Blueprint, jsonify, request
from app.services.scan_intelligence_service import process_scanned_barcode

scan_api_bp = Blueprint('scan_api', __name__, url_prefix='/api/v1/scan')

@scan_api_bp.route('/parse', methods=['GET', 'POST'])
def parse_barcode():
    if request.method == 'POST':
        payload = request.get_json() or {}
        query = payload.get('barcode')
        mode = payload.get('mode', 'Intelligence')
    else:
        query = request.args.get('barcode')
        mode = request.args.get('mode', 'Intelligence')

    if not query:
        return jsonify({'error': 'Barcode or SKU parameter is required'}), 400

    result = process_scanned_barcode(query, scan_mode=mode)
    return jsonify(result)
