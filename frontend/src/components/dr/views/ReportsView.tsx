import { useState } from "react";
import { AlertCircle, Camera, CheckCircle2, Clock, MapPin, Radio, Search, ShieldAlert, User, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface CitizenReport {
  id: string;
  source: "Citizen Mobile App" | "Field Responder Patrol" | "Drone Radar Sensor" | "Emergency Hotline 112";
  reporterName: string;
  location: string;
  coordinates: [number, number];
  type: "Waterlogging / Flooding" | "Stranded Citizens" | "Fire / Smoke Outbreak" | "Structural Cracks" | "Medical Urgent";
  urgency: "High" | "Medium" | "Low";
  status: "Pending Verification" | "Verified Critical" | "Dismissed";
  timestamp: string;
  message: string;
  attachmentsCount: number;
}

const INITIAL_REPORTS: CitizenReport[] = [
  {
    id: "RPT-2041",
    source: "Citizen Mobile App",
    reporterName: "Aarav Sharma",
    location: "Near Sheetla Devi Mandir, LBS Marg, Kurla West",
    coordinates: [72.8795, 19.0705],
    type: "Waterlogging / Flooding",
    urgency: "High",
    status: "Pending Verification",
    timestamp: "4 mins ago",
    message: "Water entering ground floor apartments rapidly. Current water depth is above waist height (~3.5 feet). 8 elderly residents trapped.",
    attachmentsCount: 2,
  },
  {
    id: "RPT-2042",
    source: "Field Responder Patrol",
    reporterName: "Sub-Inspector V. Deshmukh (Patrol 4)",
    location: "SCLR Flyover Underpass Junction, BKC Link Road",
    coordinates: [72.8680, 19.0665],
    type: "Stranded Citizens",
    urgency: "High",
    status: "Verified Critical",
    timestamp: "12 mins ago",
    message: "2 BEST buses and 5 private cars stalled in flooded underpass. Passengers standing on bus roofs waiting for inflatable boats.",
    attachmentsCount: 4,
  },
  {
    id: "RPT-2043",
    source: "Drone Radar Sensor",
    reporterName: "Autonomous UAV Scout-2",
    location: "Old Industrial Estate, Lower Parel West",
    coordinates: [72.8310, 18.9982],
    type: "Fire / Smoke Outbreak",
    urgency: "High",
    status: "Verified Critical",
    timestamp: "22 mins ago",
    message: "Thermal imagery detected elevated heat signature (480°C) and thick black smoke plume near chemical storage warehouse.",
    attachmentsCount: 1,
  },
  {
    id: "RPT-2044",
    source: "Emergency Hotline 112",
    reporterName: "Meera Kulkarni",
    location: "Sion Circle Near Transit Medical Camp",
    coordinates: [72.8630, 19.0398],
    type: "Medical Urgent",
    urgency: "High",
    status: "Pending Verification",
    timestamp: "35 mins ago",
    message: "Pregnant woman in labor needs immediate transport to Sion Hospital. Local roads submerged; normal vehicles cannot pass.",
    attachmentsCount: 0,
  },
  {
    id: "RPT-2045",
    source: "Citizen Mobile App",
    reporterName: "Rahul Patil",
    location: "Dadar TT Flyover Ramp",
    coordinates: [72.8450, 19.0190],
    type: "Structural Cracks",
    urgency: "Medium",
    status: "Pending Verification",
    timestamp: "50 mins ago",
    message: "Chunk of concrete fell from flyover underside due to heavy rainfall erosion. Traffic slowing down.",
    attachmentsCount: 3,
  },
  {
    id: "RPT-2046",
    source: "Citizen Mobile App",
    reporterName: "Unverified User",
    location: "Bandra West Promenade",
    coordinates: [72.8250, 19.0450],
    type: "Waterlogging / Flooding",
    urgency: "Low",
    status: "Dismissed",
    timestamp: "1 hour ago",
    message: "Minor sea spray near promenade bench.",
    attachmentsCount: 0,
  },
];

export default function ReportsView() {
  const [reports, setReports] = useState<CitizenReport[]>(INITIAL_REPORTS);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = reports.filter((rpt) => {
    const matchesStatus =
      filterStatus === "all" ||
      (filterStatus === "pending" && rpt.status === "Pending Verification") ||
      (filterStatus === "verified" && rpt.status === "Verified Critical") ||
      (filterStatus === "dismissed" && rpt.status === "Dismissed");
    const matchesSearch =
      rpt.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.reporterName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleVerify = (id: string) => {
    setReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "Verified Critical" as const } : r))
    );
  };

  const handleDismiss = (id: string) => {
    setReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "Dismissed" as const } : r))
    );
  };

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
              Live incoming SOS reports from citizens, field responders, emergency hotlines &amp; drone sensor feeds.
            </p>
          </div>
        </div>

        {/* Status Counters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-border bg-amber-500/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-amber-400">Pending Verification</span>
            <span className="text-base font-bold text-amber-400">
              {reports.filter((r) => r.status === "Pending Verification").length}
            </span>
          </div>
          <div className="rounded-xl border border-border bg-emerald-500/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-emerald-400">Verified Critical</span>
            <span className="text-base font-bold text-emerald-400">
              {reports.filter((r) => r.status === "Verified Critical").length}
            </span>
          </div>
          <div className="rounded-xl border border-border bg-secondary/80 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Total Incoming</span>
            <span className="text-base font-bold text-foreground">{reports.length}</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Controls */}
      <div className="flex flex-col gap-3 rounded-2xl border border-border/80 bg-card p-3.5 shadow-xs sm:flex-row sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search location, landmark or report details…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9.5 pl-9 text-xs font-medium"
          />
        </div>

        <div className="flex items-center gap-1.5">
          {[
            { id: "all", label: "All Reports" },
            { id: "pending", label: "Pending Verification" },
            { id: "verified", label: "Verified Critical" },
            { id: "dismissed", label: "Dismissed" },
          ].map((st) => (
            <button
              key={st.id}
              onClick={() => setFilterStatus(st.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                filterStatus === st.id
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Feed Grid */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((rpt) => (
          <div
            key={rpt.id}
            className="flex flex-col justify-between rounded-2xl border border-border/80 bg-card p-5 shadow-sm hover:border-cyan-500/50 transition-all hover:shadow-md"
          >
            <div>
              <div className="flex items-start justify-between gap-3 border-b border-border/50 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-muted-foreground">{rpt.id}</span>
                    <span className="rounded-md bg-secondary px-2 py-0.5 text-[11px] font-bold text-cyan-400">
                      {rpt.type}
                    </span>
                  </div>
                  <p className="mt-2 text-xs font-bold text-foreground flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-primary shrink-0" /> {rpt.location}
                  </p>
                </div>

                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                    rpt.status === "Verified Critical"
                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                      : rpt.status === "Pending Verification"
                        ? "bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {rpt.status}
                </span>
              </div>

              <p className="mt-3 text-xs font-medium text-foreground leading-relaxed bg-background/60 p-3 rounded-xl border border-border/60">
                "{rpt.message}"
              </p>

              <div className="mt-3.5 space-y-1.5 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span className="flex items-center gap-1 font-medium">
                    <User className="h-3.5 w-3.5 text-primary" /> Reporter Source:
                  </span>
                  <span className="font-bold text-foreground">{rpt.source} ({rpt.reporterName})</span>
                </div>

                <div className="flex justify-between">
                  <span className="flex items-center gap-1 font-medium">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" /> Time Received:
                  </span>
                  <span className="font-mono font-bold text-foreground">{rpt.timestamp}</span>
                </div>

                {rpt.attachmentsCount > 0 && (
                  <div className="flex items-center gap-1.5 pt-1 text-cyan-400 font-semibold">
                    <Camera className="h-3.5 w-3.5" /> {rpt.attachmentsCount} Photos / Geo-tagged Media Attached
                  </div>
                )}
              </div>
            </div>

            <div className="mt-5 border-t border-border/50 pt-3 flex gap-2">
              {rpt.status !== "Verified Critical" ? (
                <Button onClick={() => handleVerify(rpt.id)} className="flex-1 h-9 text-xs font-bold">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Verify &amp; Dispatch
                </Button>
              ) : (
                <div className="flex-1 rounded-xl bg-emerald-500/10 p-2 text-center text-xs font-bold text-emerald-400 border border-emerald-500/20">
                  ✓ Verified &amp; Added to Dispatch
                </div>
              )}
              {rpt.status !== "Dismissed" && (
                <Button onClick={() => handleDismiss(rpt.id)} variant="outline" className="h-9 px-3 text-xs font-semibold text-muted-foreground">
                  <XCircle className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
