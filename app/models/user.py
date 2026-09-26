# app/models/user.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    # Roles: super_admin, warehouse_manager, inventory_manager, procurement_manager, warehouse_operator, picker_packer, supplier, analyst, auditor
    role = db.Column(db.String(30), nullable=False, default='warehouse_operator')
    department = db.Column(db.String(50), nullable=True, default='Operations')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_display(self):
        role_titles = {
            'super_admin': 'Super Admin',
            'warehouse_manager': 'Warehouse Manager',
            'inventory_manager': 'Inventory Manager',
            'procurement_manager': 'Procurement Manager',
            'warehouse_operator': 'Warehouse Operator',
            'picker_packer': 'Picker / Packer',
            'supplier': 'Supplier Portal',
            'analyst': 'AI & Inventory Analyst',
            'auditor': 'Auditor / Compliance'
        }
        return role_titles.get(self.role, self.role.title())

    def has_permission(self, permission_name):
        # Role-based permissions matrix
        if self.role in ['super_admin', 'admin']:
            return True
        
        permission_map = {
            'inventory_manager': ['view', 'create', 'update', 'approve_reorder', 'approve_transfer', 'edit_forecast', 'manage_safety_stock', 'view_ai'],
            'warehouse_manager': ['view', 'create', 'update', 'approve_putaway', 'approve_picking', 'manage_locations', 'execute_task', 'view_ai'],
            'procurement_manager': ['view', 'approve_reorder', 'manage_suppliers', 'create_po', 'view_ai'],
            'warehouse_operator': ['view', 'execute_putaway', 'execute_picking', 'record_adjustment'],
            'picker_packer': ['view', 'execute_picking', 'execute_packing'],
            'supplier': ['view_supplier_orders', 'update_asn'],
            'analyst': ['view', 'view_ai', 'run_simulation', 'export_reports'],
            'auditor': ['view', 'view_audit_logs', 'view_ai']
        }
        user_perms = permission_map.get(self.role, ['view'])
        return permission_name in user_perms

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
