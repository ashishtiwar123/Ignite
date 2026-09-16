# Phase 2I: Resource Optimization Engine

**Objective:**
Implement a deterministic optimization engine to solve the resource allocation problem. The engine uses Google OR-Tools to maximize fulfillment of physical resource demands given finite inventory, prioritizing incidents with higher priority scores.

## 1. Scope & Core Principles
The engine strictly computes: "Given $X$ demand and $Y$ supply, how much of $Y$ goes to each incident to maximize weighted fulfillment?"

It explicitly **DOES NOT**:
- Calculate Needs or Priority (Handled by Phase 2G and 2H).
- Solve complex vehicle routing problems (VRP).
- Mix unit types (e.g. 1000 Liters of water is distinct from 1000 Metric Tons of food).
- Assume infinite supply. 

## 2. Architecture & Contracts
- **`AllocationContext`**: The canonical state object containing `incidents` (from 2H), `requirements` (from 2G), and a physical `inventory` list.
- **`ResourceAllocation`**: Represents a physical flow from `source_location_id` to `verified_incident_id`, explicitly tracking `quantity_allocated` and `quantity_unmet`.
- **`AllocationResult`**: Encapsulates all allocation decisions, the `solver_status`, and aggregate fulfillment metrics.

## 3. Optimization Model
The optimization is implemented as a Linear Program (LP) using the OR-Tools `GLOP` continuous solver.

**Objective Function**:
$$ \text{Maximize} \sum_{i \in I} \sum_{w \in W} \sum_{r \in R} \left( (\text{Priority}_i)^2 \times X_{w,i,r} \right) $$

**Constraints**:
1. **Supply Bounds**: The sum of allocations from a warehouse cannot exceed its inventory for that resource.
2. **Demand Bounds**: The sum of allocations to an incident cannot exceed its Phase 2G calculated demand.
3. **Non-negativity**: All allocations must be $\ge 0$.

### Fairness vs. Criticality
The objective dynamically weights incidents based on the square of their Priority Score (0-100). This enforces a "Priority Absolute" hierarchy in scarce conditions (e.g., an incident with 90 priority has a weight of 8100, while a 30 priority has 900. The solver will strongly bias fulfilling the 90-priority incident first before assigning remaining inventory to the 30-priority incident).

## 4. Safety & Infeasibility
- **Unit Safety**: The engine intrinsically partitions the optimization space by `(resource_type, unit)`. It is mathematically impossible for Liters to be fulfilled by Gallons inventory.
- **Unmet Demand**: If total demand exceeds supply, the solver fulfills the highest priority incidents first. Any deficit is explicitly logged as `quantity_unmet` along with an explanation, preventing silent starvation.
- **Infeasibility**: If constraints are impossible to satisfy, `solver_status` becomes `INFEASIBLE`, returning zero fabricated allocations.

## 5. Provenance & Reallocation
Every output preserves the `optimization_run_id`, allowing future Phase 3 agents to trace exactly when and why an allocation was generated. This output structure supports dynamic reallocation workflows (e.g., re-running optimization at $t_2$ when new inventory arrives).

## 6. Known Limitations
- The model uses a continuous solver (`GLOP`). For highly discrete assets (e.g., Tarpaulins), it may yield fractions (e.g., 2.5 Tarpaulins).
- Transportation constraints (vehicles, routing distances) are omitted from this MVP to isolate the core allocation logic.

## 7. Handoff
With verified incidents mathematically matched to scarce inventory, the backend intelligence layer is completely established. The system is ready for **Phase 2J — Agentic Coordination / LangGraph**.
