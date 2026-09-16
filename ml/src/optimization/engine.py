from ortools.linear_solver import pywraplp
from typing import List, Dict, Any
from collections import defaultdict
import uuid

from ml.src.optimization.schemas import (
    AllocationContext, 
    ResourceAllocation, 
    AllocationResult
)

def optimize_allocation(context: AllocationContext) -> AllocationResult:
    """
    Optimizes allocation of inventory to incident requirements using OR-Tools GLOP solver.
    """
    # 1. Indexing and setup
    # Create priority lookup (square the priority to strongly prefer critical incidents)
    priority_map = {p.verified_incident_id: p.priority_score for p in context.incidents}
    
    # Group requirements by resource_type & unit
    req_by_type = defaultdict(list)
    for r in context.requirements:
        if r.status != "CALCULATED" or r.quantity is None:
            continue
        req_by_type[(r.resource_type, r.unit)].append(r)
        
    # Group inventory by resource_type & unit
    inv_by_type = defaultdict(list)
    for i in context.inventory:
        inv_by_type[(i.resource_type, i.unit)].append(i)
        
    result = AllocationResult(optimization_run_id=context.optimization_run_id, solver_status="UNKNOWN", allocations=[])
    overall_status = "OPTIMAL"
    
    # Optimize each resource type independently to guarantee Unit Safety
    for (res_type, unit), reqs in req_by_type.items():
        invs = inv_by_type.get((res_type, unit), [])
        
        # If no inventory exists for this requirement, all is unmet
        if not invs:
            for r in reqs:
                priority = priority_map.get(r.verified_incident_id, 0.0)
                result.allocations.append(ResourceAllocation(
                    optimization_run_id=context.optimization_run_id,
                    verified_incident_id=r.verified_incident_id,
                    requirement_id=r.requirement_id,
                    source_location_id="NONE",
                    resource_type=res_type,
                    category=r.category,
                    unit=unit,
                    quantity_allocated=0.0,
                    quantity_requested=r.quantity,
                    quantity_unmet=r.quantity,
                    priority_score=priority,
                    explanation=f"0.0 {unit} allocated. {r.quantity} {unit} remains unmet because inventory was unavailable."
                ))
                result.total_requested += r.quantity
                result.total_unmet += r.quantity
            continue

        # Instantiate solver for this resource
        solver = pywraplp.Solver.CreateSolver('GLOP')
        if not solver:
            raise RuntimeError("Could not create GLOP solver.")

        # Variables: X[w][i] -> quantity from warehouse w to requirement i
        X = {}
        for w_idx, inv in enumerate(invs):
            X[w_idx] = {}
            for r_idx, req in enumerate(reqs):
                # max allocation is min(inventory, demand)
                upper_bound = min(inv.quantity_available, req.quantity)
                X[w_idx][r_idx] = solver.NumVar(0, upper_bound, f"X_{w_idx}_{r_idx}")

        # Constraint 1: Supply <= Inventory
        for w_idx, inv in enumerate(invs):
            solver.Add(sum(X[w_idx][r_idx] for r_idx in range(len(reqs))) <= inv.quantity_available)

        # Constraint 2: Total allocation to req <= Demand
        for r_idx, req in enumerate(reqs):
            solver.Add(sum(X[w_idx][r_idx] for w_idx in range(len(invs))) <= req.quantity)

        # Objective: Maximize weighted fulfillment
        objective = solver.Objective()
        for w_idx, inv in enumerate(invs):
            for r_idx, req in enumerate(reqs):
                priority = priority_map.get(req.verified_incident_id, 0.0)
                # Square the priority score (0-100) -> (0-10000) to strongly bias highest priority
                weight = (priority ** 2.0) + 1.0 
                objective.SetCoefficient(X[w_idx][r_idx], weight)
        objective.SetMaximization()

        # Solve
        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            # Process results
            for r_idx, req in enumerate(reqs):
                total_allocated = 0.0
                priority = priority_map.get(req.verified_incident_id, 0.0)
                
                # Extract allocations for this requirement
                for w_idx, inv in enumerate(invs):
                    val = X[w_idx][r_idx].solution_value()
                    if val > 0:
                        total_allocated += val
                        unmet = req.quantity - total_allocated
                        
                        alloc = ResourceAllocation(
                            optimization_run_id=context.optimization_run_id,
                            verified_incident_id=req.verified_incident_id,
                            requirement_id=req.requirement_id,
                            source_location_id=inv.location_id,
                            resource_type=res_type,
                            category=req.category,
                            unit=unit,
                            quantity_allocated=val,
                            quantity_requested=req.quantity,
                            quantity_unmet=max(0.0, req.quantity - total_allocated),
                            priority_score=priority,
                            explanation=f"Allocated {val:.1f} {unit} of {res_type} from {inv.location_id} to {req.verified_incident_id}."
                        )
                        result.allocations.append(alloc)
                
                # If fully or partially unmet, log the deficit (only if no partial allocations exist to prevent duplicate logging, or just aggregate it)
                if total_allocated < req.quantity:
                    if total_allocated == 0.0:
                        alloc = ResourceAllocation(
                            optimization_run_id=context.optimization_run_id,
                            verified_incident_id=req.verified_incident_id,
                            requirement_id=req.requirement_id,
                            source_location_id="NONE",
                            resource_type=res_type,
                            category=req.category,
                            unit=unit,
                            quantity_allocated=0.0,
                            quantity_requested=req.quantity,
                            quantity_unmet=req.quantity,
                            priority_score=priority,
                            explanation=f"0.0 {unit} allocated. {req.quantity} {unit} remains unmet due to insufficient inventory."
                        )
                        result.allocations.append(alloc)
                    else:
                        # Find the last allocation we made for this req and update its unmet explanation
                        # We already set quantity_unmet correctly above. Let's just append to its explanation.
                        last_alloc = [a for a in result.allocations if a.requirement_id == req.requirement_id][-1]
                        last_alloc.explanation += f" {req.quantity - total_allocated:.1f} {unit} remains unmet."
                
                result.total_requested += req.quantity
                result.total_allocated += total_allocated
                result.total_unmet += max(0.0, req.quantity - total_allocated)
                
            result.objective_value += objective.Value()
        else:
            overall_status = "INFEASIBLE"

    result.solver_status = overall_status
    return result
