# app/models/ai_intelligence.py
import json
from datetime import datetime
from app.extensions import db

class Forecast(db.Model):
    __tablename__ = 'forecasts'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    
    granularity = db.Column(db.String(20), default='Daily') # Daily, Weekly, Monthly
    forecast_horizon_days = db.Column(db.Integer, default=30)
    
    predicted_demand = db.Column(db.Float, nullable=False)
    lower_range = db.Column(db.Float, nullable=False)
    upper_range = db.Column(db.Float, nullable=False)
    confidence_level_pct = db.Column(db.Float, default=95.0)
    
    selected_model = db.Column(db.String(50), default='Weighted Moving Average') # Moving Average, Exponential Smoothing, ARIMA, Random Forest, XGBoost
    forecast_accuracy_pct = db.Column(db.Float, default=92.5)
    mae = db.Column(db.Float, default=1.2)
    rmse = db.Column(db.Float, default=1.8)
    mape = db.Column(db.Float, default=6.5)
    forecast_bias = db.Column(db.Float, default=0.1)
    
    influencing_factors_json = db.Column(db.Text, nullable=True) # JSON list of key signals
    last_training_date = db.Column(db.DateTime, default=datetime.utcnow)
    next_retraining_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    warehouse = db.relationship('Warehouse')

    @property
    def influencing_factors(self):
        if not self.influencing_factors_json:
            return ["Historical Sales Velocity", "Day-of-Week Seasonality", "Lead Time Variability"]
        try:
            return json.loads(self.influencing_factors_json)
        except Exception:
            return [self.influencing_factors_json]

    def __repr__(self):
        return f'<Forecast SKU:{self.product_id} Demand:{self.predicted_demand} Model:{self.selected_model}>'


class SafetyStockPolicy(db.Model):
    __tablename__ = 'safety_stock_policies'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    
    current_safety_stock = db.Column(db.Float, nullable=False)
    recommended_safety_stock = db.Column(db.Float, nullable=False)
    target_service_level_pct = db.Column(db.Float, default=95.0)
    
    demand_std_dev = db.Column(db.Float, default=2.5)
    lead_time_std_dev = db.Column(db.Float, default=1.0)
    
    reason_for_change = db.Column(db.String(255), nullable=True)
    expected_service_level_effect = db.Column(db.String(100), nullable=True)
    expected_cost_effect_annual = db.Column(db.Float, default=0.0)
    
    approval_status = db.Column(db.String(20), default='Active') # Pending, Approved, Active, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    warehouse = db.relationship('Warehouse')


class ReorderRecommendation(db.Model):
    __tablename__ = 'reorder_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    rec_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    # State values at recommendation time
    current_stock = db.Column(db.Float, nullable=False)
    reserved_stock = db.Column(db.Float, default=0.0)
    in_transit_stock = db.Column(db.Float, default=0.0)
    forecasted_demand_30d = db.Column(db.Float, nullable=False)
    safety_stock = db.Column(db.Float, nullable=False)
    reorder_point = db.Column(db.Float, nullable=False)
    
    # Recommendation details
    recommended_action = db.Column(db.String(50), default='Reorder') # Reorder, Reduce Qty, Delay Purchase, Transfer, Alternate Supplier, Liquidate
    recommended_quantity = db.Column(db.Float, nullable=False)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    expected_stockout_date = db.Column(db.DateTime, nullable=True)
    estimated_coverage_days = db.Column(db.Float, default=30.0)
    
    # Explainable AI Metadata
    problem_detected = db.Column(db.Text, nullable=False)
    data_used_json = db.Column(db.Text, nullable=True)
    predicted_impact = db.Column(db.Text, nullable=False)
    expected_benefit = db.Column(db.Text, nullable=False)
    
    urgency_level = db.Column(db.String(20), default='HIGH') # CRITICAL, HIGH, MEDIUM, LOW
    confidence_level_pct = db.Column(db.Float, default=94.0)
    financial_impact = db.Column(db.Float, default=0.0)
    
    # Approval & Execution Workflow
    approval_status = db.Column(db.String(20), default='Generated') # Generated, Reviewed, Approved, Executed, Rejected, Closed
    responsible_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejection_reason = db.Column(db.String(255), nullable=True)
    generated_po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product')
    warehouse = db.relationship('Warehouse')
    supplier = db.relationship('Supplier')
    responsible_user = db.relationship('User', foreign_keys=[responsible_user_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    generated_po = db.relationship('PurchaseOrder', foreign_keys=[generated_po_id])

    def __repr__(self):
        return f'<ReorderRecommendation {self.rec_code} Action:{self.recommended_action} Qty:{self.recommended_quantity} [{self.approval_status}]>'


class RiskEvent(db.Model):
    __tablename__ = 'risk_events'

    id = db.Column(db.Integer, primary_key=True)
    risk_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # 12 Risk Categories:
    # Stockout, Overstock, Expiry, Dead Stock, Slow Moving, Supplier Delay,
    # Demand Spike, Forecast Uncertainty, Warehouse Capacity, Location Capacity, Inventory Accuracy, Order Fulfilment
    risk_category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='High') # Critical, High, Medium, Low, Informational
    risk_score = db.Column(db.Float, default=75.0) # 0 to 100
    probability_pct = db.Column(db.Float, default=80.0)
    
    expected_date = db.Column(db.DateTime, nullable=True)
    financial_impact = db.Column(db.Float, default=0.0)
    operational_impact = db.Column(db.Text, nullable=True)
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    
    recommended_mitigation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Mitigated, Dismissed, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    warehouse = db.relationship('Warehouse')
    supplier = db.relationship('Supplier')
    location = db.relationship('Location')

    def __repr__(self):
        return f'<RiskEvent {self.risk_code} Category:{self.risk_category} Severity:{self.severity}>'


class InventoryHealthScore(db.Model):
    __tablename__ = 'inventory_health_scores'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20), default='System') # System, Warehouse, SKU
    entity_id = db.Column(db.Integer, nullable=True)
    
    overall_score = db.Column(db.Float, nullable=False) # 0 to 100
    category = db.Column(db.String(20), default='Healthy') # Healthy, Monitor, At Risk, Critical, Dead Stock
    
    # Score Components & Deductions
    stockout_deduction = db.Column(db.Float, default=0.0)
    expiry_deduction = db.Column(db.Float, default=0.0)
    overstock_deduction = db.Column(db.Float, default=0.0)
    supplier_delay_deduction = db.Column(db.Float, default=0.0)
    inaccuracy_deduction = db.Column(db.Float, default=0.0)
    space_inefficiency_deduction = db.Column(db.Float, default=0.0)
    
    explanation_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryHealthScore {self.entity_type} Score:{self.overall_score} [{self.category}]>'


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    alert_type = db.Column(db.String(50), nullable=False) # Stockout, Expiry, Capacity, Supplier Delay, Forecast Drop, Variance
    severity = db.Column(db.String(20), default='High') # Critical, High, Medium, Low, Informational
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    financial_impact = db.Column(db.Float, default=0.0)
    expected_date = db.Column(db.DateTime, nullable=True)
    recommended_action = db.Column(db.Text, nullable=True)
    
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Open') # Open, Acknowledged, In_Progress, Resolved, Dismissed
    resolution_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    warehouse = db.relationship('Warehouse')
    supplier = db.relationship('Supplier')
    assigned_user = db.relationship('User', foreign_keys=[assigned_user_id])

    def __repr__(self):
        return f'<Alert {self.alert_code} [{self.severity}] {self.title}>'


class ScenarioSimulation(db.Model):
    __tablename__ = 'scenario_simulations'

    id = db.Column(db.Integer, primary_key=True)
    scenario_name = db.Column(db.String(100), nullable=False)
    
    demand_change_pct = db.Column(db.Float, default=0.0)
    lead_time_delay_days = db.Column(db.Integer, default=0)
    safety_stock_adj_pct = db.Column(db.Float, default=0.0)
    supplier_change_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    # Simulated Outcomes JSON
    summary_results_json = db.Column(db.Text, nullable=False)
    detailed_sku_results_json = db.Column(db.Text, nullable=False)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False) # Approval, Rejection, Override, Stock_Adjustment, Policy_Change
    entity_name = db.Column(db.String(50), nullable=False)  # ReorderRecommendation, PutawayTask, Inventory, User
    entity_id = db.Column(db.String(50), nullable=False)
    
    description = db.Column(db.Text, nullable=False)
    previous_state = db.Column(db.Text, nullable=True)
    new_state = db.Column(db.Text, nullable=True)
    
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    performer = db.relationship('User')

    def __repr__(self):
        return f'<AuditLog Action:{self.action_type} Entity:{self.entity_name} Id:{self.entity_id}>'


class ModelVersion(db.Model):
    __tablename__ = 'model_versions'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False) # DemandForecast_XGB, RiskEngine_v2
    version_tag = db.Column(db.String(20), nullable=False)
    accuracy_score = db.Column(db.Float, default=93.5)
    training_samples_count = db.Column(db.Integer, default=1250)
    last_trained_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_retrain_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
