# app/routes/assistant.py
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services.assistant_service import process_assistant_natural_language_query

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/v1/assistant')

@assistant_bp.route('/query', methods=['POST'])
@login_required
def query():
    data = request.get_json() or {}
    q_text = data.get('query', '')
    if not q_text:
        return jsonify({'status': 'error', 'message': 'Query string cannot be empty.'}), 400

    res = process_assistant_natural_language_query(q_text)
    return jsonify({'status': 'success', 'data': res})
