import { useState } from "react";
import { AlertCircle, ArrowUpRight, CheckCircle2, RefreshCcw, Send, ShieldAlert, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { reassessIncident } from "@/lib/api/agents";
import type { ReassessmentResponse } from "@/lib/api/types";

interface ReassessmentModalProps {
  threadId: string;
  incidentId: string;
  onClose?: () => void;
  onReassessmentComplete?: (response: ReassessmentResponse) => void;
}

export function ReassessmentModal({
  threadId,
  incidentId,
  onClose,
  onReassessmentComplete,
}: ReassessmentModalProps) {
  const [reportText, setReportText] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ReassessmentResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportText.trim()) return;

    setLoading(true);
    setError(null);

    const reportObj = {
      source: "HOSPITAL_FIELD_REPORT",
      source_record_id: `reassess-${Date.now()}`,
      hazard_type: "Flood",
      affected_population: 3000,
      raw_text: reportText,
    };

    try {
      const res = await reassessIncident(threadId, {
        new_reports: [JSON.stringify(reportObj)],
        reassessment_reason: reason || "New field evidence submitted",
        run_id: `run-reassess-${Date.now()}`,
      });
      setResponse(res);
      if (onReassessmentComplete) onReassessmentComplete(res);
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to submit reassessment request");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-2xl space-y-4 max-w-2xl w-full">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <RefreshCcw className="h-5 w-5 text-sky-400" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-foreground">
            Phase 4G Reassessment & Dynamic Reallocation
          </h3>
        </div>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 text-xs">
            Close
          </Button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400">
          {error}
        </div>
      )}

      {!response ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1.5">
              New Evidence / Field Report:
            </label>
            <Textarea
              placeholder="e.g. Hospital flooded, 3000 victims stranded, emergency evacuation required..."
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              className="text-xs min-h-[100px] bg-muted/20"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1.5">
              Reassessment Reason:
            </label>
            <Input
              placeholder="e.g. Rapid flood escalation at central hospital"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="text-xs bg-muted/20"
            />
          </div>

          <Button type="submit" disabled={loading} className="w-full text-xs font-semibold bg-sky-600 hover:bg-sky-700">
            {loading ? (
              <RefreshCcw className="h-3.5 w-3.5 animate-spin mr-1.5" />
            ) : (
              <Send className="h-3.5 w-3.5 mr-1.5" />
            )}
            Trigger Reassessment Pipeline (LangGraph)
          </Button>
        </form>
      ) : (
        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between bg-sky-500/10 border border-sky-500/20 p-3 rounded-lg text-sky-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span className="font-semibold">Reassessment Processed</span>
            </div>
            <span className="font-mono text-[10px]">{response.reallocation_decision_status}</span>
          </div>

          {/* Assessment Diff */}
          {response.assessment_diff && (
            <div className="space-y-2 border border-border/60 p-3 rounded-lg bg-muted/10">
              <div className="font-semibold text-foreground flex items-center justify-between">
                <span>Assessment Snapshot Diff:</span>
                <span className="text-[10px] text-muted-foreground">Parent: {response.previous_assessment_id?.slice(0, 8)}...</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="bg-muted/30 p-2 rounded">
                  <span className="text-muted-foreground">Priority Score Delta:</span>
                  <span className={`font-mono font-bold ml-2 ${response.assessment_diff.priority_score_delta >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                    {response.assessment_diff.priority_score_delta >= 0 ? "+" : ""}
                    {response.assessment_diff.priority_score_delta.toFixed(2)}
                  </span>
                </div>
                <div className="bg-muted/30 p-2 rounded">
                  <span className="text-muted-foreground">Priority Level:</span>
                  <span className="font-semibold text-foreground ml-2">
                    {response.assessment_diff.current_priority_level || "UNCHANGED"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Allocation Delta */}
          {response.allocation_diff && (
            <div className="space-y-2 border border-amber-500/30 p-3 rounded-lg bg-amber-500/5">
              <div className="font-semibold text-amber-400 flex items-center justify-between">
                <span>Proposed Allocation Delta:</span>
                <span className="text-[10px] uppercase font-bold text-amber-300">
                  {response.reallocation_required ? "Reallocation Required" : "No Reallocation"}
                </span>
              </div>
              <div className="space-y-1.5">
                {response.allocation_diff.deltas.length === 0 ? (
                  <div className="text-muted-foreground italic text-[11px]">No quantitative resource changes required.</div>
                ) : (
                  response.allocation_diff.deltas.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-[11px] bg-black/20 p-2 rounded border border-border/40">
                      <div>
                        <span className="font-semibold text-foreground">{item.resource_type}</span>
                        <span className="text-[10px] text-muted-foreground ml-2">({item.source_location_id})</span>
                      </div>
                      <div className="text-right font-mono">
                        <span className={`font-bold ${item.delta_quantity > 0 ? "text-emerald-400" : item.delta_quantity < 0 ? "text-rose-400" : "text-muted-foreground"}`}>
                          {item.delta_quantity > 0 ? `+${item.delta_quantity}` : item.delta_quantity} {item.unit}
                        </span>
                        <div className="text-[9px] text-muted-foreground">
                          {item.previous_quantity} → {item.new_quantity} {item.unit}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
