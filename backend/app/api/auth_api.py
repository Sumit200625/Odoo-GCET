# backend/app/api/auth_api.py
from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/v1/auth')

@auth_api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'role_display': user.role_display
            }
        })
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@auth_api_bp.route('/me', methods=['GET'])
def current_user_info():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'name': current_user.name,
                'email': current_user.email,
                'role': current_user.role,
                'role_display': current_user.role_display
            }
        })
    return jsonify({'authenticated': False, 'user': None})

@auth_api_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})
