# app/services/putaway_slotting_engine.py
"""
Smart Slotting & Directed Put-Away Engine for StockSense.
- Recommends optimal storage locations for incoming receipts based on velocity, temperature, hazard rules, weight capacity, and distance to dispatch.
- Directed Put-Away Task Creation & Operator Scan Confirmation.
- Before-and-After Slotting Simulation (Travel distance & Picking time reduction).
"""

import uuid
from datetime import datetime
from app.extensions import db
from app.models.product import Product
from app.models.warehouse import Location, Warehouse
from app.models.operation import Receipt, PutawayTask
from app.models.stock import StockBalance, InventoryBatch
from app.services.inventory_ledger_service import record_inventory_transaction

def calculate_space_utilization_analytics(warehouse_id=None):
    """
    Computes space utilization across volume, weight, bins, and capacity status.
    """
    query = Location.query
    if warehouse_id:
        query = query.filter(Location.warehouse_id == warehouse_id)

    locations = query.all()
    total_capacity = sum(l.max_capacity for l in locations) or 1.0
    total_occupied = sum(l.occupied_quantity for l in locations)
    total_reserved = sum(l.reserved_capacity for l in locations)
    total_max_weight = sum(l.max_weight_kg for l in locations) or 1.0
    total_current_weight = sum(l.current_weight_kg for l in locations)

    vol_util_pct = round(((total_occupied + total_reserved) / total_capacity) * 100.0, 1)
    weight_util_pct = round((total_current_weight / total_max_weight) * 100.0, 1)

    location_matrix = []
    for loc in locations:
        location_matrix.append({
            'location_id': loc.id,
            'warehouse_name': loc.warehouse.name if loc.warehouse else '',
            'code': loc.code,
            'full_name': loc.full_name,
            'zone': loc.zone,
            'location_type': loc.location_type,
            'max_capacity': loc.max_capacity,
            'occupied_quantity': loc.occupied_quantity,
            'available_capacity': loc.available_capacity,
            'occupancy_pct': loc.occupancy_percentage,
            'temperature': loc.temperature_condition,
            'hazard': loc.hazard_restriction,
            'picking_frequency': loc.picking_frequency,
            'status': loc.status,
            'distance_m': loc.distance_to_dispatch_m
        })

    return {
        'total_locations': len(locations),
        'volume_utilization_pct': vol_util_pct,
        'weight_utilization_pct': weight_util_pct,
        'free_capacity_units': max(0.0, total_capacity - total_occupied - total_reserved),
        'locations': location_matrix
    }

def recommend_directed_putaway_location(product_id, quantity, batch_number=None):
    """
    Directed Put-Away Algorithm:
    Evaluates candidate locations against product velocity, weight, temperature, hazard compatibility, and distance.
    Returns ranked list of candidate locations with scoring breakdown.
    """
    product = Product.query.get_or_404(product_id)
    locations = Location.query.filter(
        Location.location_type == 'Internal',
        Location.status.in_(['Available', 'Occupied'])
    ).all()

    candidates = []
    for loc in locations:
        avail_cap = loc.available_capacity
        if avail_cap < quantity:
            continue # Insufficient volume capacity

        req_weight = (product.weight_kg or 1.0) * quantity
        if (loc.current_weight_kg + req_weight) > loc.max_weight_kg:
            continue # Exceeds weight limit

        # Temperature & Hazard Check
        if product.temperature_requirement != 'Ambient' and loc.temperature_condition != product.temperature_requirement:
            continue
        if product.hazard_class != 'None' and loc.hazard_restriction != product.hazard_class:
            continue

        # Score calculation (0 to 100)
        score = 50.0

        # Fast-moving SKUs should be close to dispatch and floor level
        if product.velocity_class == 'F' or product.abc_class == 'A':
            score += max(0.0, (50.0 - loc.distance_to_dispatch_m) * 0.8) # Distance bonus
            if loc.picking_height_level == 1:
                score += 20.0 # Floor level height bonus
        else:
            if loc.picking_height_level > 1:
                score += 15.0 # Higher racks for slow-moving

        # Existing stock consolidation bonus
        has_same_sku = any(b.product_id == product.id for b in loc.stock_balances if b.quantity > 0)
        if has_same_sku:
            score += 25.0

        score = min(100.0, max(0.0, score))

        candidates.append({
            'location_id': loc.id,
            'code': loc.code,
            'full_name': loc.full_name,
            'zone': loc.zone,
            'available_capacity': avail_cap,
            'score': round(score, 1),
            'distance_to_dispatch_m': loc.distance_to_dispatch_m,
            'picking_height_level': loc.picking_height_level,
            'reason': f"Match score {round(score,1)}: {loc.zone} (Dist: {loc.distance_to_dispatch_m}m, Avail: {avail_cap} units)"
        })

    sorted_candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
    return sorted_candidates

def generate_putaway_task(receipt_id, product_id, quantity, source_location_id, batch_number=None, user_id=1):
    """
    Generates a formal PutawayTask with recommended destination location.
    """
    recs = recommend_directed_putaway_location(product_id, quantity, batch_number)
    if not recs:
        raise ValueError("No compatible storage location with sufficient capacity found.")

    best_loc_id = recs[0]['location_id']
    task_code = f"PUT-{uuid.uuid4().hex[:8].upper()}"

    task = PutawayTask(
        task_code=task_code,
        receipt_id=receipt_id,
        product_id=product_id,
        batch_number=batch_number or 'BATCH-2026-001',
        quantity=quantity,
        source_location_id=source_location_id,
        recommended_location_id=best_loc_id,
        status='Pending',
        assigned_operator_id=user_id
    )
    
    # Reserve capacity at target location
    target_loc = Location.query.get(best_loc_id)
    target_loc.reserved_capacity += quantity

    db.session.add(task)
    db.session.commit()
    return task

def confirm_putaway_task_execution(task_id, actual_location_id, operator_user_id, override_reason=None):
    """
    Operator confirms put-away scan. Updates inventory, moves stock, logs ledger entry.
    """
    task = PutawayTask.query.get_or_404(task_id)
    if task.status == 'Completed':
        raise ValueError("Put-away task is already completed.")

    final_loc_id = actual_location_id or task.recommended_location_id
    
    # Release reserved capacity on recommended location
    rec_loc = Location.query.get(task.recommended_location_id)
    rec_loc.reserved_capacity = max(0.0, rec_loc.reserved_capacity - task.quantity)

    # Perform Stock Transfer from Source (Staging) to Destination Location
    record_inventory_transaction(
        product_id=task.product_id,
        quantity_change=task.quantity,
        operation_type='Put-away',
        reference=task.task_code,
        created_by=operator_user_id,
        source_location_id=task.source_location_id,
        destination_location_id=final_loc_id,
        batch_number=task.batch_number,
        reason=override_reason or "Directed Put-away Completed"
    )

    task.actual_location_id = final_loc_id
    task.status = 'Completed' if final_loc_id == task.recommended_location_id else 'Overridden'
    task.override_reason = override_reason
    task.completed_at = datetime.utcnow()

    db.session.commit()
    return task

def simulate_slotting_rebalancing():
    """
    Simulates slotting optimization by recommending fast-moving SKU relocations closer to dispatch.
    Returns before-and-after distance and picking time savings.
    """
    products = Product.query.filter(Product.velocity_class == 'F').all()
    simulations = []

    total_dist_before = 0.0
    total_dist_after = 0.0

    for p in products:
        for b in p.stock_balances:
            if b.quantity > 0:
                curr_loc = b.location
                recs = recommend_directed_putaway_location(p.id, b.quantity)
                if recs and recs[0]['location_id'] != curr_loc.id:
                    rec_loc = Location.query.get(recs[0]['location_id'])
                    dist_saved = max(0.0, curr_loc.distance_to_dispatch_m - rec_loc.distance_to_dispatch_m)
                    
                    total_dist_before += curr_loc.distance_to_dispatch_m
                    total_dist_after += rec_loc.distance_to_dispatch_m

                    simulations.append({
                        'product_id': p.id,
                        'sku': p.sku,
                        'name': p.name,
                        'current_location': curr_loc.full_name,
                        'current_distance_m': curr_loc.distance_to_dispatch_m,
                        'recommended_location': rec_loc.full_name,
                        'recommended_distance_m': rec_loc.distance_to_dispatch_m,
                        'travel_distance_saved_m': dist_saved,
                        'estimated_time_savings_pct': round((dist_saved / max(1.0, curr_loc.distance_to_dispatch_m)) * 100.0, 1),
                        'rationale': f"Fast-moving {p.velocity_class} SKU relocated closer to dispatch bay."
                    })

    time_savings_pct = round(((total_dist_before - total_dist_after) / max(1.0, total_dist_before)) * 100.0, 1) if total_dist_before > 0 else 0.0

    return {
        'total_relocations_recommended': len(simulations),
        'total_distance_before_m': total_dist_before,
        'total_distance_after_m': total_dist_after,
        'overall_picking_time_savings_pct': time_savings_pct,
        'relocation_details': simulations
    }
