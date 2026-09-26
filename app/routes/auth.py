# app/routes/auth.py
import random
from sqlalchemy import func
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.utils.decorators import role_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter(func.lower(User.email) == email).first()
        if not user or not user.check_password(password):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}! ({user.role.capitalize()} Role)', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'staff')

        if not name or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        existing_user = User.query.filter(func.lower(User.email) == email).first()
        if existing_user:
            flash('Email address is already registered.', 'danger')
            return render_template('auth/register.html', name=name, role=role)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Account created successfully! Logged in as {user.role.capitalize()}.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'request_otp':
            email = request.form.get('email', '').strip().lower()
            user = User.query.filter(func.lower(User.email) == email).first()
            if not user:
                flash('No account found with that email address.', 'danger')
                return render_template('auth/reset_password.html', step=1)

            otp = str(random.randint(100000, 999999))
            session['reset_email'] = email
            session['reset_otp'] = otp

            flash(f'MOCK OTP GENERATED: {otp} — Enter this code below to proceed.', 'warning')
            return render_template('auth/reset_password.html', step=2, email=email, demo_otp=otp)

        elif action == 'verify_otp':
            otp_entered = request.form.get('otp', '').strip()
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            session_otp = session.get('reset_otp')
            email = session.get('reset_email')

            if not session_otp or not email:
                flash('Password reset session expired. Please request a new OTP.', 'danger')
                return render_template('auth/reset_password.html', step=1)

            if otp_entered != session_otp:
                flash('Invalid OTP code. Please try again.', 'danger')
                return render_template('auth/reset_password.html', step=2, email=email, demo_otp=session_otp)

            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('auth/reset_password.html', step=2, email=email, demo_otp=session_otp)

            user = User.query.filter(func.lower(User.email) == email).first()
            if user:
                user.set_password(new_password)
                db.session.commit()
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                flash('Password reset successful! Please log in with your new password.', 'success')
                return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', step=1)

# VIEW ALL USERS (Admin & Manager)
@auth_bp.route('/users')
@login_required
@role_required('admin', 'manager')
def users_list():
    users = User.query.order_by(User.id).all()
    return render_template('auth/users.html', users=users)

# MANAGE USER ROLE (Admin Only)
@auth_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@role_required('admin')
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'manager', 'staff']:
        user.role = new_role
        db.session.commit()
        flash(f"User {user.email} role updated to '{new_role.capitalize()}'.", 'success')
    else:
        flash('Invalid role selected.', 'danger')
    return redirect(url_for('auth.users_list'))
