import { useState } from "react";
import { AlertCircle, Camera, CheckCircle2, Clock, MapPin, Radio, Search, Send, ShieldAlert, User, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createReport } from "@/lib/api/reports";
import { runAgent } from "@/lib/api/agents";
import type { ReportResponse, AgentRunResponse } from "@/lib/api/types";

export interface CitizenReport {
  id: string;
  source: string;
  reporterName: string;
  location: string;
  type: string;
  status: string;
  timestamp: string;
  message: string;
}

const INITIAL_REPORTS: CitizenReport[] = [
  {
    id: "RPT-2041",
    source: "Mumbai Municipal Emergency Cell",
    reporterName: "Control Room Operator",
    location: "Mumbai Lowlands",
    type: "Flood",
    status: "Verified Critical",
    timestamp: "10:42 AM",
    message: "Severe waterlogging reported across low-lying residential areas. Multiple families require evacuation.",
  },
  {
    id: "RPT-2042",
    source: "Field Response Unit",
    reporterName: "Ground Recon Team 1",
    location: "Mumbai Command Area",
    type: "Flood",
    status: "Verified Critical",
    timestamp: "10:51 AM",
    message: "Ground teams report rising water levels near the command area. Approximately 1200 residents affected.",
  },
  {
    id: "RPT-2043",
    source: "City Hospital Coordination Desk",
    reporterName: "Dr. A. Mehta (Chief Medical Officer)",
    location: "EOC Medical Sector",
    type: "Medical Emergency",
    status: "Verified Critical",
    timestamp: "11:03 AM",
    message: "Hospital access is partially obstructed. Medical evacuation support and emergency supplies are required.",
  },
  {
    id: "RPT-2044",
    source: "NGO Relief Network",
    reporterName: "Disaster Relief Coordinator",
    location: "Relief Transit Depot",
    type: "Supply Request",
    status: "Pending Allocation",
    timestamp: "11:17 AM",
    message: "Emergency drinking water and food supplies requested for displaced families.",
  },
];

export default function ReportsView() {
  const [reports, setReports] = useState<CitizenReport[]>(INITIAL_REPORTS);
  const [searchQuery, setSearchQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [reportSuccess, setReportSuccess] = useState<string | null>(null);

  // New report form state
  const [hazardType, setHazardType] = useState("Flood");
  const [locationName, setLocationName] = useState("Zone C");
  const [population, setPopulation] = useState("500");
  const [rawText, setRawText] = useState("");

  const handleSubmitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;

    setSubmitting(true);
    setSubmitError(null);
    setReportSuccess(null);

    const reportPayload = {
      source: "FIELD_REPORTER_UI",
      source_record_id: `rpt-${Date.now()}`,
      hazard_type: hazardType,
      location_name: locationName,
      affected_population: Number(population) || 500,
      raw_text: rawText,
    };

    try {
      const res: ReportResponse = await createReport(reportPayload);
      
      // Also trigger backend agent run pipeline
      const agentRes: AgentRunResponse = await runAgent({
        run_id: `run-${Date.now()}`,
        raw_reports: [JSON.stringify(reportPayload)],
      });

      setReportSuccess(`Report Ingested! Backend Response: ${res.message}. Agent Pipeline Status: ${agentRes.status}`);

      // Add to local UI feed
      setReports((prev) => [
        {
          id: res.report_id.slice(0, 8),
          source: "Field Reporter UI",
          reporterName: "Current Dispatcher",
          location: locationName,
          type: hazardType,
          status: "Processing (FastAPI)",
          timestamp: "Just now",
          message: rawText,
        },
        ...prev,
      ]);
      setRawText("");
    } catch (err: any) {
      setSubmitError(err.detail || err.message || "Failed to submit report to backend");
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = reports.filter((rpt) => {
    return (
      rpt.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-5 p-5">
      {/* Header Banner */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:flex-row lg:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
            <Radio className="h-5.5 w-5.5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Dynamic Field &amp; Citizen Incident Reports</h1>
            <p className="text-xs font-medium text-muted-foreground">
              Submit SOS reports directly to FastAPI backend (`POST /reports` &amp; `POST /agents/run`).
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Left Column (2 Cols): Feed & Search */}
        <div className="space-y-4 lg:col-span-2">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search reports by location or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9.5 pl-9 text-xs font-medium"
            />
          </div>

          <div className="space-y-3">
            {filtered.map((rpt) => (
              <div key={rpt.id} className="rounded-2xl border border-border/80 bg-card p-4 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-muted-foreground">{rpt.id}</span>
                    <span className="bg-cyan-500/15 text-cyan-400 font-bold px-2 py-0.5 rounded text-[11px]">{rpt.type}</span>
                    <span className="text-muted-foreground flex items-center gap-1"><MapPin className="h-3 w-3 text-primary" /> {rpt.location}</span>
                  </div>
                  <span className="bg-amber-500/15 text-amber-400 font-bold px-2 py-0.5 rounded text-[10px]">{rpt.status}</span>
                </div>
                <p className="text-xs text-foreground bg-background/60 p-2.5 rounded-lg border border-border/40">"{rpt.message}"</p>
                <div className="flex justify-between text-[11px] text-muted-foreground pt-1">
                  <span>Source: {rpt.source} ({rpt.reporterName})</span>
                  <span>Received: {rpt.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column (1 Col): Real Report Submission Form */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-4">
          <div className="border-b border-border/50 pb-3">
            <h2 className="text-sm font-bold text-foreground">Submit Real Field Report</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Triggers FastAPI validation and LangGraph incident detection.</p>
          </div>

          {submitError && (
            <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400">
              {submitError}
            </div>
          )}

          {reportSuccess && (
            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 text-xs text-emerald-400">
              {reportSuccess}
            </div>
          )}

          <form onSubmit={handleSubmitReport} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-muted-foreground block mb-1">Hazard Type:</label>
              <Input
                value={hazardType}
                onChange={(e) => setHazardType(e.target.value)}
                className="h-8.5 text-xs bg-muted/20"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-muted-foreground block mb-1">Location Name:</label>
              <Input
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                className="h-8.5 text-xs bg-muted/20"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-muted-foreground block mb-1">Affected Population:</label>
              <Input
                type="number"
                value={population}
                onChange={(e) => setPopulation(e.target.value)}
                className="h-8.5 text-xs bg-muted/20"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-muted-foreground block mb-1">Raw Report Details:</label>
              <Textarea
                placeholder="Describe situation in detail..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="text-xs min-h-[90px] bg-muted/20"
                required
              />
            </div>

            <Button type="submit" disabled={submitting} className="w-full text-xs font-bold bg-primary">
              {submitting ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Send className="h-3.5 w-3.5 mr-1" />}
              Submit to FastAPI Endpoint (`POST /reports`)
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
