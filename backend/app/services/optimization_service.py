from ml.src.optimization.schemas import AllocationContext, AllocationResult

class OptimizationService:
    @staticmethod
    def run_optimization(context_data: dict) -> AllocationResult:
        """
        Thin wrapper for OR-Tools GLOP optimization engine
        """
        context = AllocationContext(**context_data)
        # Mocking the call to the engine to just validate the boundary
        # engine.optimize(context)
        return AllocationResult(
            optimization_run_id=context.optimization_run_id,
            solver_status="OPTIMAL",
            allocations=[]
        )
