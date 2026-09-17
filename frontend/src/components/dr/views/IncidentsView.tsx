import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, Clock, Filter, MapPin, RefreshCw, Search, ShieldAlert, Users, Zap, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Scenario } from "@/lib/scenario";
import { getIncidents, getIncidentAssessment } from "@/lib/api/incidents";
import type { IncidentSummaryResponse, AssessmentResponse } from "@/lib/api/types";
import { ReassessmentModal } from "@/components/dr/ReassessmentModal";

interface IncidentsViewProps {
  scenario: Scenario;
  activeThreadId?: string;
}

export default function IncidentsView({ scenario, activeThreadId = "run-demo-1" }: IncidentsViewProps) {
  const [incidents, setIncidents] = useState<IncidentSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showReassessment, setShowReassessment] = useState(false);

  const fetchIncidents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidents();
      setIncidents(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].incident_id);
      }
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to load real incidents from backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setAssessment(null);
      return;
    }
    const fetchAssessment = async () => {
      setAssessmentLoading(true);
      try {
        const assData = await getIncidentAssessment(selectedId);
        setAssessment(assData);
      } catch (err) {
        setAssessment(null);
      } finally {
        setAssessmentLoading(false);
      }
    };
    fetchAssessment();
  }, [selectedId]);

  const selectedIncident = incidents.find((i) => i.incident_id === selectedId) || incidents[0];

  const filtered = incidents.filter((inc) => {
    const matchesSearch =
      inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.hazard_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-5 p-5">
      {/* Header Banner & Quick Stats */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:flex-row lg:items-center">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-destructive/15 text-destructive">
              <AlertTriangle className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-foreground">Incident Command & Log Registry</h1>
              <p className="text-xs font-medium text-muted-foreground">
                Real-time records from FastAPI backend (`/incidents`) and ML pipeline intelligence.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={fetchIncidents} variant="outline" size="sm" className="text-xs font-semibold">
            <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> Refresh Backend
          </Button>
          <div className="rounded-xl border border-border bg-secondary/70 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Backend Incidents</span>
            <span className="text-base font-bold text-foreground">{incidents.length}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-medium text-rose-400">
          Backend Integration Notice: {error}
        </div>
      )}

      {/* Controls & Main Split View */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Left Column (2 Cols on lg): Incident List */}
        <div className="space-y-4 lg:col-span-2">
          {/* Search Bar */}
          <div className="flex flex-col gap-3 rounded-xl border border-border/80 bg-card p-3 shadow-xs sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search incident ID or hazard type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 pl-9 text-xs font-medium"
              />
            </div>
          </div>

          {/* Incident Cards List */}
          {loading ? (
            <div className="flex items-center justify-center py-12 text-xs text-muted-foreground">
              <RefreshCw className="h-5 w-5 animate-spin mr-2 text-primary" /> Fetching incidents from backend...
            </div>
          ) : filtered.length === 0 ? (
            <div className="rounded-2xl border border-border bg-card p-8 text-center text-xs text-muted-foreground">
              No backend incidents found. Submit a report from the Home or Reports page to trigger LangGraph detection.
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((inc) => {
                const isSelected = selectedIncident && inc.incident_id === selectedIncident.incident_id;

                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => setSelectedId(inc.incident_id)}
                    className={`cursor-pointer rounded-2xl border p-4 transition-all ${
                      isSelected
                        ? "border-primary bg-card ring-1 ring-primary/40 shadow-md"
                        : "border-border/80 bg-card/60 hover:bg-card hover:border-border"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-muted-foreground">
                            {inc.incident_id.slice(0, 8)}...
                          </span>
                          <span className="rounded-md border border-sky-500/30 bg-sky-500/15 px-2 py-0.5 text-[11px] font-bold uppercase text-sky-400">
                            {inc.hazard_type}
                          </span>
                        </div>
                        <h3 className="mt-1.5 text-sm font-bold text-foreground">
                          {inc.hazard_type} Incident
                        </h3>
                      </div>

                      <span className="shrink-0 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-bold text-emerald-400">
                        {inc.status}
                      </span>
                    </div>

                    <div className="mt-3.5 flex flex-wrap items-center justify-between border-t border-border/50 pt-2.5 text-xs font-medium text-muted-foreground">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1 font-mono text-[11px]">
                          <MapPin className="h-3.5 w-3.5 text-primary" /> Lat: {inc.centroid_latitude ?? "N/A"}, Lon: {inc.centroid_longitude ?? "N/A"}
                        </span>
                      </div>
                      <span className="flex items-center gap-1 font-mono text-[11px]">
                        <Clock className="h-3.5 w-3.5 text-muted-foreground" /> Observed: {new Date(inc.first_observed_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column (1 Col on lg): Selected Incident Assessment Details */}
        {selectedIncident && (
          <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-primary">Backend Assessment</span>
                <h2 className="text-sm font-mono font-bold text-foreground mt-0.5">{selectedIncident.incident_id}</h2>
              </div>
              <span className="rounded-lg bg-sky-500/15 text-sky-400 px-2.5 py-1 text-xs font-bold uppercase">
                {selectedIncident.hazard_type}
              </span>
            </div>

            {assessmentLoading ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin inline mr-1 text-primary" /> Loading ML Assessment...
              </div>
            ) : assessment ? (
              <div className="space-y-3 text-xs">
                {/* Verification */}
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground font-medium">Verification Status:</span>
                  <span className="font-bold text-emerald-400 uppercase">{assessment.verification_status}</span>
                </div>

                {/* Severity */}
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground font-medium">Severity Score:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {assessment.severity?.severity_score ?? (assessment.severity?.message || "UNSUPPORTED")}
                  </span>
                </div>

                {/* Trajectory */}
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground font-medium">Trajectory:</span>
                  <span className="font-semibold text-foreground">
                    {assessment.trajectory?.trajectory || assessment.trajectory?.status || "INSUFFICIENT_EVIDENCE"}
                  </span>
                </div>

                {/* Priority */}
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground font-medium">Priority Score:</span>
                  <span className="font-mono font-bold text-destructive">
                    {assessment.priority?.priority_score ?? "CALCULATED ON PIPELINE"}
                  </span>
                </div>

                {/* Needs Status */}
                <div className="py-1.5">
                  <span className="text-muted-foreground font-medium block mb-1">Sphere Needs Assessment:</span>
                  <div className="bg-muted/30 p-2 rounded text-[11px] text-muted-foreground font-mono">
                    {JSON.stringify(assessment.needs)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground italic py-4">
                Assessment details not computed yet for this candidate.
              </div>
            )}

            {/* Reassessment CTA */}
            <div className="border-t border-border/50 pt-4">
              <Button
                onClick={() => setShowReassessment(true)}
                className="w-full text-xs font-semibold bg-sky-600 hover:bg-sky-700"
              >
                <RefreshCcw className="h-3.5 w-3.5 mr-1.5" /> Reassess Incident (Phase 4G Evidence)
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Reassessment Modal */}
      {showReassessment && selectedIncident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <ReassessmentModal
            threadId={activeThreadId}
            incidentId={selectedIncident.incident_id}
            onClose={() => setShowReassessment(false)}
            onReassessmentComplete={() => fetchIncidents()}
          />
        </div>
      )}
    </div>
  );
}
