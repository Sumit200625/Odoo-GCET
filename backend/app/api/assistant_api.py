# backend/app/api/assistant_api.py
from flask import Blueprint, jsonify, request
from app.services.assistant_service import process_assistant_natural_language_query

assistant_api_bp = Blueprint('assistant_api', __name__, url_prefix='/api/v1/assistant')

@assistant_api_bp.route('/query', methods=['POST'])
def query_assistant():
    payload = request.get_json() or {}
    q = payload.get('query', '')
    if not q:
        return jsonify({'error': 'Query text is required'}), 400

    result = process_assistant_natural_language_query(q)
    return jsonify(result)
