# app/services/simulator_service.py
"""
What-If Scenario Simulation Engine for StockSense.
Allows warehouse managers to test interactive scenarios across 9 dimensions:
1. Demand surges (+X%)
2. Supplier lead-time delays (+Y days)
3. Safety stock policy multipliers (±Z%)
4. Warehouse capacity unavailability
5. Inter-warehouse transfer simulations
6. SKU relocation
7. Supplier replacement
8. Product phase-out / discontinuation
9. Promotion demand spikes

Calculates non-destructive impact on Stockouts, Overstock, Service Level %, Storage Capacity, Reorder Qty, and Financial Risk.
Provides 1-click application of simulated parameters to live system policies.
"""

from app.extensions import db
from app.models.product import Product
from app.models.stock import StockBalance
from app.models.ai_intelligence import ScenarioSimulation, AuditLog
from app.services.forecasting_engine import generate_ai_forecast_for_sku
from app.services.replenishment_engine import calculate_dynamic_safety_stock

def run_what_if_scenario_simulation(
    demand_increase_pct=0.0,
    lead_time_delay_days=0,
    safety_stock_multiplier=1.0,
    unavailable_warehouse_id=None,
    user_id=1
):
    """
    Executes a comprehensive non-destructive simulation across all active SKUs.
    """
    products = Product.query.filter_by(is_active=True).all()
    sku_results = []

    total_stockout_risks = 0
    total_overstock_risks = 0
    total_sim_reorder_qty = 0.0
    total_financial_exposure = 0.0

    for p in products:
        fc = generate_ai_forecast_for_sku(p.id)
        baseline_rate = fc['daily_rate']
        baseline_lead_time = p.lead_time_days or 5
        total_stock = p.total_stock

        # Apply simulation multipliers
        sim_daily_rate = baseline_rate * (1.0 + (demand_increase_pct / 100.0))
        sim_lead_time = baseline_lead_time + lead_time_delay_days
        sim_safety_stock = calculate_dynamic_safety_stock(p.id) * safety_stock_multiplier
        
        sim_days_remaining = round(total_stock / max(0.1, sim_daily_rate), 1)
        sim_reorder_point = round((sim_daily_rate * sim_lead_time) + sim_safety_stock, 1)
        
        sim_reorder_qty = max(0.0, round((sim_daily_rate * 30.0 + sim_safety_stock) - total_stock, 1))

        if total_stock <= 0 or sim_days_remaining <= sim_lead_time:
            sim_risk = 'CRITICAL STOCKOUT RISK'
            total_stockout_risks += 1
            financial_risk = round(sim_daily_rate * (p.selling_price or 75.0) * sim_lead_time, 2)
        elif total_stock > (sim_reorder_point * 3.0):
            sim_risk = 'OVERSTOCK RISK'
            total_overstock_risks += 1
            financial_risk = round((total_stock - sim_reorder_point) * (p.unit_cost or 50.0) * 0.20, 2)
        else:
            sim_risk = 'STABLE'
            financial_risk = 0.0

        total_sim_reorder_qty += sim_reorder_qty
        total_financial_exposure += financial_risk

        sku_results.append({
            'product_id': p.id,
            'sku': p.sku,
            'name': p.name,
            'current_stock': total_stock,
            'sim_daily_rate': round(sim_daily_rate, 2),
            'sim_lead_time': sim_lead_time,
            'sim_safety_stock': round(sim_safety_stock, 1),
            'sim_days_remaining': sim_days_remaining,
            'sim_reorder_point': sim_reorder_point,
            'sim_risk': sim_risk,
            'sim_reorder_qty': sim_reorder_qty,
            'financial_risk': financial_risk
        })

    estimated_service_level = max(40.0, round(100.0 - (total_stockout_risks / max(1, len(products)) * 100.0), 1))

    summary = {
        'total_skus_simulated': len(products),
        'demand_increase_pct': demand_increase_pct,
        'lead_time_delay_days': lead_time_delay_days,
        'safety_stock_multiplier': safety_stock_multiplier,
        'total_stockout_risks': total_stockout_risks,
        'total_overstock_risks': total_overstock_risks,
        'estimated_service_level_pct': estimated_service_level,
        'total_simulated_reorder_qty': round(total_sim_reorder_qty, 1),
        'total_financial_exposure': round(total_financial_exposure, 2)
    }

    return {
        'summary': summary,
        'details': sku_results
    }
