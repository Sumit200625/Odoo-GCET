# app/utils/rbac.py
import re
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    return re.match(EMAIL_REGEX, email.strip()) is not None

def role_required(*roles):
    """
    Role-Based Access Control (RBAC) decorator.
    Restricts view access to specified user roles (e.g. 'admin', 'manager', 'staff').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access StockSense.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                allowed = ', '.join([r.capitalize() for r in roles])
                flash(
                    f"Access Denied: Your role ({current_user.role.capitalize()}) does not have permission to access this resource. "
                    f"Required permission level: [{allowed}].",
                    'danger'
                )
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
