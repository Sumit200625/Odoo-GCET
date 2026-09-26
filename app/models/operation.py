# app/models/operation.py
from datetime import datetime
from app.extensions import db

# ==========================================
# INBOUND & PURCHASE ORDER ENTITIES
# ==========================================

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    
    # Workflow: Draft, Submitted, Approved, Sent, Partial, Received, Closed, Canceled
    status = db.Column(db.String(30), default='Draft')
    total_amount = db.Column(db.Float, default=0.0)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    actual_delivery_date = db.Column(db.DateTime, nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier')
    warehouse = db.relationship('Warehouse')
    creator = db.relationship('User', foreign_keys=[created_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number} [{self.status}]>'

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    ordered_quantity = db.Column(db.Float, nullable=False)
    received_quantity = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float, default=0.0)

    product = db.relationship('Product')


class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    status = db.Column(db.String(30), default='Draft') # Draft, Arrived, Inspecting, Received, Putaway_Pending, Done, Canceled
    asn_number = db.Column(db.String(50), nullable=True) # Advance Shipment Notice
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    supplier = db.relationship('Supplier', foreign_keys=[supplier_id])
    destination_location = db.relationship('Location', foreign_keys=[destination_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('ReceiptLine', backref='receipt', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Receipt {self.reference} [{self.status}]>'

class ReceiptLine(db.Model):
    __tablename__ = 'receipt_lines'

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    ordered_quantity = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Float, nullable=False)            # Received Quantity
    damaged_quantity = db.Column(db.Float, default=0.0)
    rejected_quantity = db.Column(db.Float, default=0.0)
    accepted_quantity = db.Column(db.Float, default=0.0)
    
    batch_number = db.Column(db.String(50), default='BATCH-2026-001')
    expiry_date = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')


# ==========================================
# OUTBOUND & SALES ORDER ENTITIES
# ==========================================

class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_priority = db.Column(db.String(20), default='Normal') # High, Normal, Low
    
    status = db.Column(db.String(30), default='Draft') # Draft, Reserved, Picking, Packed, Dispatched, Cancelled
    promised_delivery_date = db.Column(db.DateTime, nullable=True)
    shipping_address = db.Column(db.String(255), nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SalesOrder {self.order_number} [{self.status}]>'

class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    ordered_quantity = db.Column(db.Float, nullable=False)
    allocated_quantity = db.Column(db.Float, default=0.0)
    picked_quantity = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)

    product = db.relationship('Product')


class Delivery(db.Model):
    __tablename__ = 'deliveries'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    status = db.Column(db.String(30), default='Draft') # Draft, Ready, Picking, Packed, Done, Canceled
    promised_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='NORMAL') # HIGH, NORMAL, LOW
    picking_method = db.Column(db.String(30), default='Single') # Single, Batch, Zone, Wave, Cluster
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('DeliveryLine', backref='delivery', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Delivery {self.reference} [{self.status}]>'

class DeliveryLine(db.Model):
    __tablename__ = 'delivery_lines'

    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey('deliveries.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    batch_allocated = db.Column(db.String(50), nullable=True)

    product = db.relationship('Product')


# ==========================================
# WAREHOUSE TASK ENTITIES (PUT-AWAY & PICKING)
# ==========================================

class PutawayTask(db.Model):
    __tablename__ = 'putaway_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    recommended_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    actual_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    
    priority = db.Column(db.String(20), default='Medium') # High, Medium, Low
    status = db.Column(db.String(30), default='Pending') # Pending, Assigned, Completed, Overridden, Canceled
    assigned_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    override_reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    recommended_location = db.relationship('Location', foreign_keys=[recommended_location_id])
    actual_location = db.relationship('Location', foreign_keys=[actual_location_id])
    operator = db.relationship('User', foreign_keys=[assigned_operator_id])

    def __repr__(self):
        return f'<PutawayTask {self.task_code} [{self.status}]>'


class PickTask(db.Model):
    __tablename__ = 'pick_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey('deliveries.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    requested_quantity = db.Column(db.Float, nullable=False)
    picked_quantity = db.Column(db.Float, default=0.0)
    
    pick_path_sequence = db.Column(db.Integer, default=1)
    status = db.Column(db.String(30), default='Pending') # Pending, In_Progress, Completed, Short_Picked, Canceled
    assigned_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    short_pick_reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    operator = db.relationship('User', foreign_keys=[assigned_operator_id])

    def __repr__(self):
        return f'<PickTask {self.task_code} [{self.status}]>'


# ==========================================
# TRANSFERS & ADJUSTMENTS
# ==========================================

class Transfer(db.Model):
    __tablename__ = 'transfers'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    source_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    status = db.Column(db.String(30), default='Draft') # Draft, Approved, Waiting, Done, Canceled
    
    transfer_reason = db.Column(db.String(255), default='Internal Optimization')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    source_location = db.relationship('Location', foreign_keys=[source_location_id])
    destination_location = db.relationship('Location', foreign_keys=[destination_location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('TransferLine', backref='transfer', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Transfer {self.reference} [{self.status}]>'

class TransferLine(db.Model):
    __tablename__ = 'transfer_lines'

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('transfers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)

    product = db.relationship('Product')


class Adjustment(db.Model):
    __tablename__ = 'adjustments'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default='Draft') # Draft, Pending_Approval, Done, Canceled
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime, nullable=True)

    location = db.relationship('Location', foreign_keys=[location_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    lines = db.relationship('AdjustmentLine', backref='adjustment', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Adjustment {self.reference} [{self.status}]>'

class AdjustmentLine(db.Model):
    __tablename__ = 'adjustment_lines'

    id = db.Column(db.Integer, primary_key=True)
    adjustment_id = db.Column(db.Integer, db.ForeignKey('adjustments.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    recorded_quantity = db.Column(db.Float, nullable=False)
    counted_quantity = db.Column(db.Float, nullable=False)
    difference = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')
