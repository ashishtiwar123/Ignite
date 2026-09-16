import { useState } from "react";
import { AlertTriangle, CheckCircle, Clock, Filter, MapPin, Search, ShieldAlert, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import type { Scenario } from "@/lib/scenario";

interface IncidentsViewProps {
  scenario: Scenario;
}

export interface IncidentRecord {
  id: string;
  title: string;
  zone: string;
  severity: "critical" | "high" | "moderate" | "low";
  affected: number;
  reportedAt: string;
  status: "Unassigned" | "In Progress" | "Resolved";
  category: "Submergence" | "Structural Damage" | "Fire Hazard" | "Medical Emergency" | "Road Blockade";
  assignedUnits: string[];
  description: string;
}

const INITIAL_INCIDENTS: IncidentRecord[] = [
  {
    id: "INC-801",
    title: "Severe Waterlogging & Stranded Commuters near Kurla Station",
    zone: "Kurla West",
    severity: "critical",
    affected: 450,
    reportedAt: "12 mins ago",
    status: "In Progress",
    category: "Submergence",
    assignedUnits: ["Rescue Team Alpha", "Boat Unit 2"],
    description: "Water levels reached 2.2 meters near railway subway. 450 commuters stranded inside station premises needing boat evacuation.",
  },
  {
    id: "INC-802",
    title: "Transformer Short-Circuit & Minor Wildfire at LBS Marg",
    zone: "Bandra East",
    severity: "high",
    affected: 180,
    reportedAt: "28 mins ago",
    status: "In Progress",
    category: "Fire Hazard",
    assignedUnits: ["Fire Tender 4", "NDRF Platoon B"],
    description: "Substation transformer blown up due to water seepage. Localized flames spreading to adjacent dense foliage.",
  },
  {
    id: "INC-803",
    title: "Wall Collapse Threat near Old Mill Compound",
    zone: "Lower Parel",
    severity: "moderate",
    affected: 85,
    reportedAt: "45 mins ago",
    status: "Unassigned",
    category: "Structural Damage",
    assignedUnits: [],
    description: "Compound boundary wall showing structural cracks and lean. Precautionary evacuation of 85 residents initiated.",
  },
  {
    id: "INC-804",
    title: "Emergency Medical Evacuation at Sion Transit Camp",
    zone: "Sion",
    severity: "high",
    affected: 120,
    reportedAt: "1 hour ago",
    status: "In Progress",
    category: "Medical Emergency",
    assignedUnits: ["Medical Team Bravo", "Sion Ambulance 1"],
    description: "Elderly patients requiring oxygen support stranded due to flooded access road. Ambulance unit dispatched via high-ground route.",
  },
  {
    id: "INC-805",
    title: "Tree Fallen & Arterial Road Blockade at SCLR Junction",
    zone: "BKC",
    severity: "low",
    affected: 40,
    reportedAt: "2 hours ago",
    status: "Resolved",
    category: "Road Blockade",
    assignedUnits: ["Municipal Chainsaw Crew 1"],
    description: "Large banyan tree fallen across 2 lanes. Cleared by municipal response team; traffic restored.",
  },
];

export default function IncidentsView({ scenario }: IncidentsViewProps) {
  const [incidents, setIncidents] = useState<IncidentRecord[]>(INITIAL_INCIDENTS);
  const [selectedId, setSelectedId] = useState<string>(INITIAL_INCIDENTS[0]!.id);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const selected = incidents.find((i) => i.id === selectedId) || incidents[0]!;

  const filtered = incidents.filter((inc) => {
    const matchesSev = filterSeverity === "all" || inc.severity === filterSeverity;
    const matchesSearch =
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.zone.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesSearch;
  });

  const handleResolve = (id: string) => {
    setIncidents((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: "Resolved" as const } : item))
    );
  };

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
                Real-time records of active emergency calls, hazard reports & dispatch logs for {scenario.disasterType} scenario.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-border bg-secondary/70 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Total Reported</span>
            <span className="text-base font-bold text-foreground">{incidents.length}</span>
          </div>
          <div className="rounded-xl border border-border bg-destructive/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-destructive">Critical & High</span>
            <span className="text-base font-bold text-destructive">
              {incidents.filter((i) => i.severity === "critical" || i.severity === "high").length}
            </span>
          </div>
          <div className="rounded-xl border border-border bg-emerald-500/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-emerald-400">Resolved</span>
            <span className="text-base font-bold text-emerald-400">
              {incidents.filter((i) => i.status === "Resolved").length}
            </span>
          </div>
        </div>
      </div>

      {/* Controls & Main Split View */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Left Column (2 Cols on lg): Incident List */}
        <div className="space-y-4 lg:col-span-2">
          {/* Search & Filter Bar */}
          <div className="flex flex-col gap-3 rounded-xl border border-border/80 bg-card p-3 shadow-xs sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search incident title, zone or category…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 pl-9 text-xs font-medium"
              />
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <Filter className="h-4 w-4 text-muted-foreground ml-1" />
              {(["all", "critical", "high", "moderate", "low"] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-semibold capitalize transition-colors ${
                    filterSeverity === sev
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "bg-secondary text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          {/* Incident Cards List */}
          <div className="space-y-3">
            {filtered.map((inc) => {
              const isSelected = inc.id === selected.id;
              const sevBadge =
                inc.severity === "critical"
                  ? "bg-destructive/15 text-destructive border-destructive/30"
                  : inc.severity === "high"
                    ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
                    : inc.severity === "moderate"
                      ? "bg-sky-500/15 text-sky-400 border-sky-500/30"
                      : "bg-muted text-muted-foreground border-border";

              return (
                <div
                  key={inc.id}
                  onClick={() => setSelectedId(inc.id)}
                  className={`cursor-pointer rounded-2xl border p-4 transition-all ${
                    isSelected
                      ? "border-primary bg-card ring-1 ring-primary/40 shadow-md"
                      : "border-border/80 bg-card/60 hover:bg-card hover:border-border"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-muted-foreground">{inc.id}</span>
                        <span className={`rounded-md border px-2 py-0.5 text-[11px] font-bold uppercase ${sevBadge}`}>
                          {inc.severity}
                        </span>
                        <span className="rounded-md bg-secondary px-2 py-0.5 text-[11px] font-medium text-foreground">
                          {inc.category}
                        </span>
                      </div>
                      <h3 className="mt-1.5 text-sm font-bold text-foreground">{inc.title}</h3>
                    </div>

                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        inc.status === "Resolved"
                          ? "bg-emerald-500/15 text-emerald-400"
                          : inc.status === "In Progress"
                            ? "bg-primary/15 text-primary"
                            : "bg-amber-500/15 text-amber-400"
                      }`}
                    >
                      {inc.status}
                    </span>
                  </div>

                  <p className="mt-2 line-clamp-2 text-xs font-medium text-muted-foreground">{inc.description}</p>

                  <div className="mt-3.5 flex flex-wrap items-center justify-between border-t border-border/50 pt-2.5 text-xs font-medium text-muted-foreground">
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-primary" /> {inc.zone}
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="h-3.5 w-3.5 text-primary" /> {inc.affected} affected
                      </span>
                    </div>
                    <span className="flex items-center gap-1 font-mono text-[11px]">
                      <Clock className="h-3.5 w-3.5 text-muted-foreground" /> {inc.reportedAt}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (1 Col on lg): Selected Incident Detail Inspector */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-primary">Inspector Panel</span>
              <h2 className="text-base font-bold text-foreground mt-0.5">{selected.id}</h2>
            </div>
            <span
              className={`rounded-lg px-2.5 py-1 text-xs font-bold uppercase ${
                selected.severity === "critical"
                  ? "bg-destructive/15 text-destructive"
                  : "bg-amber-500/15 text-amber-400"
              }`}
            >
              {selected.severity}
            </span>
          </div>

          <div>
            <h3 className="text-sm font-bold text-foreground">{selected.title}</h3>
            <p className="mt-2 text-xs font-medium text-muted-foreground leading-relaxed">
              {selected.description}
            </p>
          </div>

          <div className="space-y-2 border-t border-border/50 pt-3 text-xs">
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Location Zone:</span>
              <span className="font-semibold text-foreground">{selected.zone}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Category:</span>
              <span className="font-semibold text-foreground">{selected.category}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">People Affected:</span>
              <span className="font-mono font-bold text-foreground">{selected.affected} citizens</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted-foreground">Reported Time:</span>
              <span className="font-mono font-semibold text-foreground">{selected.reportedAt}</span>
            </div>
          </div>

          <div className="border-t border-border/50 pt-3">
            <span className="text-xs font-bold text-foreground block mb-2">Assigned Rescue Units ({selected.assignedUnits.length})</span>
            {selected.assignedUnits.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {selected.assignedUnits.map((unit) => (
                  <span key={unit} className="rounded-md bg-secondary px-2.5 py-1 text-xs font-semibold text-primary">
                    🛡️ {unit}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-amber-400 font-medium">⚠️ No units assigned yet. Immediate dispatch recommended.</p>
            )}
          </div>

          <div className="space-y-2 border-t border-border/50 pt-4">
            {selected.status !== "Resolved" ? (
              <Button onClick={() => handleResolve(selected.id)} className="w-full h-9.5 text-xs font-bold">
                <CheckCircle className="h-4 w-4 mr-1.5" /> Mark Incident Resolved
              </Button>
            ) : (
              <div className="rounded-xl bg-emerald-500/10 p-2.5 text-center text-xs font-bold text-emerald-400 border border-emerald-500/20">
                ✓ Incident Marked Resolved
              </div>
            )}
            <Button variant="outline" className="w-full h-9 text-xs font-semibold">
              <ShieldAlert className="h-4 w-4 mr-1.5 text-destructive" /> Escalate to NDRF Command
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
