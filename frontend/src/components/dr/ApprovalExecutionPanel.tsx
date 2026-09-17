import { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertOctagon,
  Play,
  ShieldAlert,
  Check,
  RefreshCw,
  FileText,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import {
  submitReview,
  executeProposal,
  getIncidentGovernance,
} from "@/lib/api/agents";

import type {
  AgentRunResponse,
  ExecutionResponse,
  AllocationRecord,
} from "@/lib/api/types";

import { isDemoMode, DEMO_THREAD_ID, DEMO_OPT_RUN_ID, DEMO_GOVERNANCE } from "@/lib/demoScenario";

interface ApprovalExecutionPanelProps {
  threadId: string;
  incidentId: string;
  allocations: AllocationRecord[];
  currentApprovalState?: string;
  onStateChange?: () => void;
}

export function ApprovalExecutionPanel({
  threadId: initialThreadId,
  incidentId,
  allocations,
  currentApprovalState = "PENDING",
  onStateChange,
}: ApprovalExecutionPanelProps) {
  const [decision, setDecision] = useState<
    "APPROVED" | "REJECTED" | "REVISION_REQUESTED"
  >("APPROVED");

  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [approvalStatus, setApprovalStatus] =
    useState<string>(currentApprovalState);

  const [executionResult, setExecutionResult] =
    useState<ExecutionResponse | null>(null);

  const [executing, setExecuting] = useState(false);

  // Local LangGraph thread ID.
  // This must remain separate from optimizationRunId.
  const [threadId, setThreadId] = useState<string>(
    initialThreadId || (isDemoMode() ? DEMO_THREAD_ID : "")
  );

  // Optimization run ID used by the execution service.
  const [optimizationRunId, setOptimizationRunId] =
    useState<string>(isDemoMode() ? DEMO_OPT_RUN_ID : "");

  /*
   * Synchronize local threadId from parent prop.
   */
  useEffect(() => {
    if (isDemoMode()) {
      setThreadId(initialThreadId || DEMO_THREAD_ID);
      setOptimizationRunId(DEMO_OPT_RUN_ID);
      return;
    }
    setThreadId(initialThreadId || "");
  }, [initialThreadId]);

  /*
   * Hydrate persisted governance state for an existing incident.
   */
  useEffect(() => {
    if (!incidentId) return;

    if (isDemoMode()) {
      setApprovalStatus((prev) => (prev && prev !== "PENDING" ? prev : DEMO_GOVERNANCE.approval_status));
      setThreadId(DEMO_THREAD_ID);
      setOptimizationRunId(DEMO_OPT_RUN_ID);
      return;
    }

    let isMounted = true;

    getIncidentGovernance(incidentId)
      .then((gov) => {
        if (!isMounted) return;

        if (
          gov.approval_status &&
          gov.approval_status !== "NONE"
        ) {
          setApprovalStatus(gov.approval_status);
        }

        if (gov.thread_id) {
          setThreadId(gov.thread_id);
        }

        if (gov.optimization_run_id) {
          setOptimizationRunId(
            gov.optimization_run_id
          );
        }

        if (
          gov.execution_status &&
          gov.execution_status !== "UNEXECUTED"
        ) {
          setExecutionResult({
            execution_id:
              gov.execution_id || "N/A",
            status: gov.execution_status,
            optimization_run_id:
              gov.optimization_run_id,
            approval_id: gov.approval_id,
            incident_id: gov.incident_id,
            deducted_resources:
              gov.deducted_resources || [],
            errors: gov.errors || [],
          });
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [incidentId]);

  /*
   * Submit human governance decision.
   */
  const handleReview = async () => {
    const activeThread = threadId || (isDemoMode() ? DEMO_THREAD_ID : "");
    if (!activeThread) {
      setError(
        "No active LangGraph thread ID available for review"
      );
      return;
    }

    setLoading(true);
    setError(null);

    if (isDemoMode()) {
      setTimeout(() => {
        setApprovalStatus(decision);
        setLoading(false);
        if (onStateChange) onStateChange();
      }, 350);
      return;
    }

    try {
      const res: AgentRunResponse =
        await submitReview(activeThread, {
          decision,
          reason:
            reason ||
            `Decision ${decision} submitted via UI`,
        });

      /*
       * Update local approval state immediately.
       */
      setApprovalStatus(
        res.human_approval_state || decision
      );

      /*
       * Preserve authoritative thread ID returned by backend.
       */
      if (res.thread_id) {
        setThreadId(res.thread_id);
      }

      /*
       * Ask dashboard to refresh persisted governance state.
       */
      if (onStateChange) {
        onStateChange();
      }
    } catch (err: any) {
      setError(
        err?.detail ||
          err?.message ||
          "Failed to submit review decision"
      );
    } finally {
      setLoading(false);
    }
  };

  /*
   * Execute the approved allocation proposal.
   */
  const handleExecute = async () => {
    const activeThread = threadId || (isDemoMode() ? DEMO_THREAD_ID : "");
    if (!activeThread) {
      setError(
        "No active LangGraph thread ID available for execution"
      );
      return;
    }

    setExecuting(true);
    setError(null);

    if (isDemoMode()) {
      setTimeout(() => {
        setExecutionResult({
          execution_id: "exec-mumbai-demo-001",
          status: "EXECUTED",
          optimization_run_id: optimizationRunId || DEMO_OPT_RUN_ID,
          approval_id: "appr-mumbai-demo-001",
          incident_id: incidentId,
          deducted_resources: [
            {
              resource_id: "r1",
              location_id: "Mumbai Central Depot",
              resource_type: "Portable Water",
              category: "WATER",
              quantity_deducted: 7500,
              unit: "L",
              previous_quantity: 12000,
              new_quantity: 4500,
            },
            {
              resource_id: "r2",
              location_id: "Mumbai Relief Warehouse",
              resource_type: "Cereal / Food",
              category: "FOOD",
              quantity_deducted: 0.225,
              unit: "MT",
              previous_quantity: 0.8,
              new_quantity: 0.575,
            },
          ],
          errors: [],
        });
        setExecuting(false);
        if (onStateChange) onStateChange();
      }, 450);
      return;
    }

    try {
      const res: ExecutionResponse =
        await executeProposal(activeThread, {
          incident_id: incidentId,
          optimization_run_id:
            optimizationRunId || undefined,
        });

      setExecutionResult(res);

      if (
        res.status === "NOT_APPROVED" ||
        res.status === "FAILED"
      ) {
        setError(
          res.errors.length > 0
            ? res.errors.join(", ")
            : `Execution rejected with status '${res.status}'`
        );
      }

      if (onStateChange) {
        onStateChange();
      }
    } catch (err: any) {
      setError(
        err?.detail ||
          err?.message ||
          "Execution failed"
      );
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card/60 p-5 backdrop-blur-md">

      {/* ========================================================= */}
      {/* HEADER */}
      {/* ========================================================= */}

      <div className="flex items-center justify-between border-b border-border/50 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-400" />

          <h3 className="text-sm font-semibold tracking-wide uppercase text-foreground">
            Human-in-the-Loop Governance & Execution
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">
            Status:
          </span>

          <span
            className={`font-semibold px-2 py-0.5 rounded-full text-xs ${
              approvalStatus === "APPROVED"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : approvalStatus === "REJECTED"
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
            }`}
          >
            {approvalStatus}
          </span>
        </div>
      </div>

      {/* ========================================================= */}
      {/* NO ACTIVE THREAD WARNING */}
      {/* ========================================================= */}

      {!threadId && (
        <div className="mb-4 rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-xs text-amber-400 font-medium">
          No active optimization proposal session.
        </div>
      )}

      {/* ========================================================= */}
      {/* ERROR */}
      {/* ========================================================= */}

      {error && (
        <div className="mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400">
          {error}
        </div>
      )}

      {/* ========================================================= */}
      {/* PROPOSAL SUMMARY */}
      {/* ========================================================= */}

      <div className="mb-4 space-y-2">

        <div className="text-xs font-medium text-muted-foreground">
          Proposed Allocations ({allocations.length} items):
        </div>

        {allocations.length === 0 ? (
          <div className="text-xs text-muted-foreground italic bg-muted/20 p-3 rounded-lg">
            No active allocations proposed yet.
          </div>
        ) : (
          <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">

            {allocations.map((alloc) => (
              <div
                key={alloc.allocation_id}
                className="flex items-center justify-between text-xs bg-muted/40 p-2.5 rounded-md border border-border/40"
              >

                <div>
                  <span className="font-semibold text-foreground">
                    {alloc.resource_type}
                  </span>

                  <span className="text-muted-foreground ml-2">
                    ({alloc.category || "GENERAL"})
                  </span>

                  <div className="text-[10px] text-muted-foreground">
                    From: {alloc.source_location_id}
                  </div>
                </div>

                <div className="text-right">

                  <span className="font-mono font-bold text-amber-400">
                    {alloc.quantity_allocated}{" "}
                    {alloc.unit}
                  </span>

                  <div className="text-[10px] text-muted-foreground">
                    Req: {alloc.quantity_requested}{" "}
                    {alloc.unit}
                  </div>

                </div>
              </div>
            ))}

          </div>
        )}

      </div>

      {/* ========================================================= */}
      {/* HUMAN REVIEW ACTIONS */}
      {/* ========================================================= */}

      {approvalStatus !== "APPROVED" && (
        <div className="space-y-3 border-t border-border/40 pt-4">

          <div className="text-xs font-semibold text-foreground">
            Submit Decision:
          </div>

          <div className="grid grid-cols-3 gap-2">

            {/* APPROVE */}
            <Button
              type="button"
              variant={
                decision === "APPROVED"
                  ? "default"
                  : "outline"
              }
              size="sm"
              disabled={!threadId || loading}
              className={
                decision === "APPROVED"
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : ""
              }
              onClick={() =>
                setDecision("APPROVED")
              }
            >
              <Check className="h-3.5 w-3.5 mr-1" />
              Approve
            </Button>

            {/* REJECT */}
            <Button
              type="button"
              variant={
                decision === "REJECTED"
                  ? "default"
                  : "outline"
              }
              size="sm"
              disabled={!threadId || loading}
              className={
                decision === "REJECTED"
                  ? "bg-rose-600 hover:bg-rose-700 text-white"
                  : ""
              }
              onClick={() =>
                setDecision("REJECTED")
              }
            >
              <XCircle className="h-3.5 w-3.5 mr-1" />
              Reject
            </Button>

            {/* REVISION */}
            <Button
              type="button"
              variant={
                decision === "REVISION_REQUESTED"
                  ? "default"
                  : "outline"
              }
              size="sm"
              disabled={!threadId || loading}
              className={
                decision === "REVISION_REQUESTED"
                  ? "bg-amber-600 hover:bg-amber-700 text-white"
                  : ""
              }
              onClick={() =>
                setDecision(
                  "REVISION_REQUESTED"
                )
              }
            >
              <AlertOctagon className="h-3.5 w-3.5 mr-1" />
              Revise
            </Button>

          </div>

          {/* GOVERNANCE REASON */}
          <Textarea
            placeholder="Reason or notes for governance log..."
            value={reason}
            onChange={(e) =>
              setReason(e.target.value)
            }
            className="text-xs h-16 bg-muted/20"
          />

          {/* SUBMIT DECISION */}
          <Button
            type="button"
            className="w-full text-xs font-semibold"
            disabled={loading || !threadId}
            onClick={handleReview}
          >
            {loading ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" />
            ) : (
              <FileText className="h-3.5 w-3.5 mr-1" />
            )}

            Submit Decision to Backend
          </Button>

        </div>
      )}

      {/* ========================================================= */}
      {/* EXECUTION BOUNDARY */}
      {/* ========================================================= */}

      {approvalStatus === "APPROVED" && (
        <div className="space-y-3 border-t border-border/40 pt-4">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold text-emerald-400">
              Proposal Approved
            </span>

            <span className="text-[10px] text-muted-foreground">
              Execution Gate Enabled
            </span>

          </div>

          {!executionResult ||
          (
            executionResult.status !== "EXECUTED" &&
            executionResult.status !== "ALREADY_EXECUTED"
          ) ? (

            <Button
              type="button"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
              disabled={
                executing || !threadId
              }
              onClick={handleExecute}
            >

              {executing ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" />
              ) : (
                <Play className="h-3.5 w-3.5 mr-1 fill-current" />
              )}

              Execute Allocation Proposal
            </Button>

          ) : (

            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-3 space-y-2 text-xs">

              <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                Execution Status:{" "}
                {executionResult.status}
              </div>

              <div className="text-[11px] text-muted-foreground">
                Execution ID:{" "}
                {executionResult.execution_id}
              </div>

              {executionResult.deducted_resources.length >
                0 && (

                <div className="space-y-1 pt-1">

                  <div className="text-[11px] font-semibold text-foreground">
                    Deducted Resources:
                  </div>

                  {executionResult.deducted_resources.map(
                    (d, i) => (
                      <div
                        key={i}
                        className="flex justify-between text-[10px] text-muted-foreground bg-black/20 p-1.5 rounded"
                      >

                        <span>
                          {d.resource_type} (
                          {d.location_id})
                        </span>

                        <span className="font-mono font-bold text-emerald-400">
                          -{d.quantity_deducted}{" "}
                          {d.unit}
                        </span>

                      </div>
                    )
                  )}

                </div>
              )}

            </div>
          )}

        </div>
      )}

    </div>
  );
}