import { useState } from "react";
import { CheckCircle2, XCircle, AlertOctagon, Play, ShieldAlert, Check, RefreshCw, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { submitReview, executeProposal } from "@/lib/api/agents";
import type { AgentRunResponse, ExecutionResponse, AllocationRecord } from "@/lib/api/types";

interface ApprovalExecutionPanelProps {
  threadId: string;
  incidentId: string;
  allocations: AllocationRecord[];
  currentApprovalState?: string;
  onStateChange?: () => void;
}

export function ApprovalExecutionPanel({
  threadId,
  incidentId,
  allocations,
  currentApprovalState = "PENDING",
  onStateChange,
}: ApprovalExecutionPanelProps) {
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED" | "REVISION_REQUESTED">("APPROVED");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<string>(currentApprovalState);
  const [executionResult, setExecutionResult] = useState<ExecutionResponse | null>(null);
  const [executing, setExecuting] = useState(false);

  const handleReview = async () => {
    if (!threadId) return;
    setLoading(true);
    setError(null);
    try {
      const res: AgentRunResponse = await submitReview(threadId, {
        decision,
        reason: reason || `Decision ${decision} submitted via UI`,
      });
      setApprovalStatus(res.human_approval_state || decision);
      if (onStateChange) onStateChange();
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to submit review decision");
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!threadId) return;
    setExecuting(true);
    setError(null);
    try {
      const res: ExecutionResponse = await executeProposal(threadId, {
        incident_id: incidentId,
      });
      setExecutionResult(res);
      if (onStateChange) onStateChange();
    } catch (err: any) {
      setError(err.detail || err.message || "Execution failed");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-border/50 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-400" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-foreground">
            Human-in-the-Loop Governance & Execution
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">Status:</span>
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

      {error && (
        <div className="mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400">
          {error}
        </div>
      )}

      {/* Proposal Summary */}
      <div className="mb-4 space-y-2">
        <div className="text-xs font-medium text-muted-foreground">Proposed Allocations ({allocations.length} items):</div>
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
                  <span className="font-semibold text-foreground">{alloc.resource_type}</span>
                  <span className="text-muted-foreground ml-2">({alloc.category || "GENERAL"})</span>
                  <div className="text-[10px] text-muted-foreground">From: {alloc.source_location_id}</div>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-amber-400">
                    {alloc.quantity_allocated} {alloc.unit}
                  </span>
                  <div className="text-[10px] text-muted-foreground">Req: {alloc.quantity_requested} {alloc.unit}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Actions */}
      {approvalStatus !== "APPROVED" && (
        <div className="space-y-3 border-t border-border/40 pt-4">
          <div className="text-xs font-semibold text-foreground">Submit Decision:</div>
          <div className="grid grid-cols-3 gap-2">
            <Button
              type="button"
              variant={decision === "APPROVED" ? "default" : "outline"}
              size="sm"
              className={decision === "APPROVED" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
              onClick={() => setDecision("APPROVED")}
            >
              <Check className="h-3.5 w-3.5 mr-1" /> Approve
            </Button>
            <Button
              type="button"
              variant={decision === "REJECTED" ? "default" : "outline"}
              size="sm"
              className={decision === "REJECTED" ? "bg-rose-600 hover:bg-rose-700 text-white" : ""}
              onClick={() => setDecision("REJECTED")}
            >
              <XCircle className="h-3.5 w-3.5 mr-1" /> Reject
            </Button>
            <Button
              type="button"
              variant={decision === "REVISION_REQUESTED" ? "default" : "outline"}
              size="sm"
              className={decision === "REVISION_REQUESTED" ? "bg-amber-600 hover:bg-amber-700 text-white" : ""}
              onClick={() => setDecision("REVISION_REQUESTED")}
            >
              <AlertOctagon className="h-3.5 w-3.5 mr-1" /> Revise
            </Button>
          </div>

          <Textarea
            placeholder="Reason or notes for governance log..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="text-xs h-16 bg-muted/20"
          />

          <Button
            type="button"
            className="w-full text-xs font-semibold"
            disabled={loading}
            onClick={handleReview}
          >
            {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <FileText className="h-3.5 w-3.5 mr-1" />}
            Submit Decision to Backend
          </Button>
        </div>
      )}

      {/* Execution Boundary */}
      {approvalStatus === "APPROVED" && (
        <div className="space-y-3 border-t border-border/40 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400">Proposal Approved</span>
            <span className="text-[10px] text-muted-foreground">Execution Gate Enabled</span>
          </div>

          {!executionResult ? (
            <Button
              type="button"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
              disabled={executing}
              onClick={handleExecute}
            >
              {executing ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" />
              ) : (
                <Play className="h-3.5 w-3.5 mr-1 fill-current" />
              )}
              Execute Allocation Proposal (Phase 4F Service)
            </Button>
          ) : (
            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-3 space-y-2 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                Execution Status: {executionResult.status}
              </div>
              <div className="text-[11px] text-muted-foreground">Execution ID: {executionResult.execution_id}</div>
              {executionResult.deducted_resources.length > 0 && (
                <div className="space-y-1 pt-1">
                  <div className="text-[11px] font-semibold text-foreground">Deducted Resources:</div>
                  {executionResult.deducted_resources.map((d, i) => (
                    <div key={i} className="flex justify-between text-[10px] text-muted-foreground bg-black/20 p-1.5 rounded">
                      <span>{d.resource_type} ({d.location_id})</span>
                      <span className="font-mono font-bold text-emerald-400">-{d.quantity_deducted} {d.unit}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
