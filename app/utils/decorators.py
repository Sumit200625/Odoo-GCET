# app/utils/decorators.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Role-Based Access Control (RBAC) Decorator.
    Usage: @role_required('admin', 'manager')
    If unauthorized, redirects to dashboard with flash message:
    "You do not have permission to perform this action."
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('Access Denied: You do not have permission to perform this action.', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
