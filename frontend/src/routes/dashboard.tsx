import { createFileRoute, Link } from "@tanstack/react-router";
import { ClientOnly } from "@tanstack/react-router";
import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import {
  AlertTriangle,
  Boxes,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  LayoutDashboard,
  Layers,
  Mountain,
  Route as RouteIcon,
  Satellite,
  Settings,
  Sparkles,
  Truck,
  Users,
  Wind,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import type { LayerToggles, MapMode } from "@/components/dr/DisasterMap";
import {
  DISASTER_TYPES,
  aiRecommendation,
  cycloneDetailsFor,
  deploymentsFor,
  facilitiesFor,
  formatClock,
  incidentsFor,
  loadScenario,
  timelineFor,
  zoneOf,
  type Incident,
  type Scenario,
} from "@/lib/scenario";

import IncidentsView from "@/components/dr/views/IncidentsView";
import ResourcesView from "@/components/dr/views/ResourcesView";
import AgenciesView from "@/components/dr/views/AgenciesView";
import ReportsView from "@/components/dr/views/ReportsView";
import SettingsView from "@/components/dr/views/SettingsView";
import { ApprovalExecutionPanel } from "@/components/dr/ApprovalExecutionPanel";

const DisasterMap = lazy(() => import("@/components/dr/DisasterMap"));

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Command Dashboard — ResQAI Disaster Response" },
      {
        name: "description",
        content:
          "Live disaster command centre: map overlays, resource deployment routes, shelters, AI recommendations and an event timeline.",
      },
      { property: "og:title", content: "ResQAI Command Dashboard" },
      {
        property: "og:description",
        content:
          "Monitor disaster zones, aid routes and AI-prioritised actions on satellite and 3D maps.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "incidents", label: "Incidents", icon: AlertTriangle },
  { id: "resources", label: "Resources", icon: Truck },
  { id: "agencies", label: "Agencies", icon: Users },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
];

function Dashboard() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mode, setMode] = useState<MapMode>("satellite");
  const [activeNav, setActiveNav] = useState("dashboard");
  const [showSettings, setShowSettings] = useState(false);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [backendIncidents, setBackendIncidents] = useState<import("@/lib/api/types").IncidentSummaryResponse[]>([]);
  const [activeAllocations, setActiveAllocations] = useState<import("@/lib/api/types").AllocationRecord[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string>("run-demo-1");
  const [layers, setLayers] = useState<LayerToggles>({
    zones: true,
    routes: true,
    resources: true,
    facilities: true,
    incidents: true,
  });
  const shellRef = useRef<HTMLDivElement | null>(null);

  const refreshBackendData = async () => {
    try {
      const incs = await import("@/lib/api/incidents").then((m) => m.getIncidents());
      setBackendIncidents(incs);
      if (incs.length > 0) {
        const allocs = await import("@/lib/api/allocations").then((m) => m.getIncidentAllocations(incs[0].incident_id));
        setActiveAllocations(allocs);
      }
    } catch {
      // Backend polling fallback handling
    }
  };

  useEffect(() => {
    setScenario(loadScenario());
    refreshBackendData();
  }, []);

  useEffect(() => {
    if (!scenario || !shellRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from(".panel-in", {
        y: 14,
        opacity: 0,
        duration: 0.5,
        stagger: 0.07,
        ease: "power2.out",
      });
    }, shellRef);
    return () => ctx.revert();
  }, [scenario]);

  const derived = useMemo(() => {
    if (!scenario) return null;
    return {
      zone: zoneOf(scenario),
      type: DISASTER_TYPES.find((d) => d.id === scenario.disasterType)!,
      deployments: deploymentsFor(scenario),
      facilities: facilitiesFor(scenario),
      incidents: incidentsFor(scenario),
      timeline: timelineFor(scenario),
      ai: aiRecommendation(scenario),
    };
  }, [scenario]);

  if (!scenario || !derived) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        Loading operations data…
      </div>
    );
  }

  const detail = selected ?? derived.incidents[0]!;

  return (
    <div ref={shellRef} className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      {/* top bar */}
      <header className="flex h-16 shrink-0 items-center gap-4 border-b border-border bg-card px-5">
        <Link to="/" className="flex items-center gap-2.5">
          <img src="/logo.png" alt="ResQAI Logo" className="h-9 w-9 object-contain rounded-md" />
          <span className="hidden leading-tight sm:block">
            <span className="block text-base font-bold text-foreground">ResQAI</span>
            <span className="block text-xs text-muted-foreground font-medium">
              Disaster Response System
            </span>
          </span>
        </Link>
        <span className="flex items-center gap-2 rounded-md bg-destructive/15 px-3 py-1 text-xs font-bold uppercase tracking-wider text-destructive">
          <span className="live-dot h-2 w-2 rounded-full bg-destructive animate-pulse" /> Live
        </span>
        <div className="min-w-0">
          <h1 className="truncate text-base font-bold text-foreground">
            {derived.zone.name} · {derived.type.label}
          </h1>
          <p className="truncate text-xs font-medium text-muted-foreground">
            {derived.type.overlay} · severity {scenario.severity}
          </p>
        </div>
        <div className="ml-auto hidden items-center gap-3 lg:flex">
          <Stat label="Active Incidents" value={String(derived.incidents.length)} tone="alert" />
          <Stat
            label="People Affected"
            value={scenario.affectedPopulation.toLocaleString()}
            tone="primary"
          />
          <Stat label="Units Deployed" value={String(derived.deployments.length)} tone="warning" />
        </div>
        <div className="text-right text-xs leading-tight text-muted-foreground">
          <span className="block font-mono text-base font-bold text-foreground">
            {formatClock(scenario.startedAt)}
          </span>
          <span className="font-medium text-muted-foreground">EOC Mumbai</span>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* sidebar */}
        <aside
          className={`relative flex shrink-0 flex-col border-r border-border bg-card transition-[width] duration-300 ${
            collapsed ? "w-16" : "w-60"
          }`}
        >
          <nav className="flex-1 space-y-1.5 p-2.5">
            {NAV.map((item) => {
              const active = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  title={item.label}
                  className={`flex w-full items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-semibold transition-colors ${
                    active
                      ? "bg-primary/15 text-primary font-bold shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <item.icon className="h-4.5 w-4.5 shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </nav>
          {!collapsed && (
            <div className="border-t border-border p-4 text-xs text-muted-foreground">
              <p className="font-display text-sm font-bold text-foreground">India</p>
              Disaster Ready · Stronger Together
            </div>
          )}
          <Button
            variant="secondary"
            size="icon"
            onClick={() => setCollapsed((c) => !c)}
            className="absolute -right-3 top-3 h-6 w-6 rounded-full border border-border shadow-sm"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronLeft className="h-3.5 w-3.5" />
            )}
          </Button>
        </aside>

        {/* main scrolling content container */}
        <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
          {activeNav === "incidents" ? (
            <IncidentsView scenario={scenario} />
          ) : activeNav === "resources" ? (
            <ResourcesView />
          ) : activeNav === "agencies" ? (
            <AgenciesView />
          ) : activeNav === "reports" ? (
            <ReportsView />
          ) : activeNav === "settings" ? (
            <SettingsView />
          ) : (
            <>

          {/* Top Row: Map + Right-Side Key Metrics Panel side-by-side */}
          <div className="flex flex-col gap-3.5 p-3.5 lg:flex-row">
            {/* Map Frame */}
            <section className="relative flex-1 min-w-0 h-[52vh] min-h-[460px]">
              <div className="relative h-full w-full overflow-hidden rounded-2xl border border-border/80 bg-card shadow-xl">
                <ClientOnly
                  fallback={
                    <div className="grid h-full place-items-center text-sm text-muted-foreground">
                      Preparing map…
                    </div>
                  }
                >
                  <Suspense
                    fallback={
                      <div className="grid h-full place-items-center text-sm text-muted-foreground">
                        Loading map layers…
                      </div>
                    }
                  >
                    <DisasterMap
                      scenario={scenario}
                      mode={mode}
                      layers={layers}
                      onSelectIncident={setSelected}
                      backendIncidents={backendIncidents}
                    />
                  </Suspense>
                </ClientOnly>

                {/* Cyclone Forecast HUD Card - matching reference design */}
                {scenario.disasterType === "cyclone" && (() => {
                  const cycloneInfo = cycloneDetailsFor(scenario);
                  return (
                    <div className="pointer-events-auto absolute left-4 top-4 z-10 w-72 rounded-xl border border-border/80 bg-card/95 p-3.5 shadow-2xl backdrop-blur-md">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400 ring-1 ring-purple-500/30">
                          <Wind className="h-5.5 w-5.5 animate-spin" style={{ animationDuration: "8s" }} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold text-foreground">{cycloneInfo.name}</h3>
                            <span className="rounded bg-purple-500/20 px-2 py-0.5 text-xs font-bold text-purple-300">
                              {cycloneInfo.category}
                            </span>
                          </div>
                          <p className="text-xs font-medium text-muted-foreground">Cyclone Forecast Track</p>
                        </div>
                      </div>
                      <div className="mt-3 space-y-2 border-t border-border/50 pt-2.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground font-medium">Wind Speed:</span>
                          <span className="font-mono font-bold text-foreground">{cycloneInfo.windSpeed}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground font-medium">ETA to Landfall:</span>
                          <span className="font-mono font-bold text-amber-400">{cycloneInfo.etaHours} hours</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground font-medium">Impact Probability:</span>
                          <span className="font-mono font-bold text-purple-400">{cycloneInfo.probability}</span>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* map controls overlay - sleek top-right position */}
                <div className="pointer-events-none absolute right-4 top-4 z-10 flex flex-col items-end gap-2">
                  <div className="pointer-events-auto flex items-center gap-2 rounded-xl border border-border/80 bg-card/90 p-1.5 shadow-lg backdrop-blur-md">
                    <ModeButton
                      active={mode === "satellite"}
                      onClick={() => setMode("satellite")}
                      icon={<Satellite className="h-4 w-4" />}
                      label="Satellite"
                    />
                    <ModeButton
                      active={mode === "3d"}
                      onClick={() => setMode("3d")}
                      icon={<Mountain className="h-4 w-4" />}
                      label="3D View"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowSettings((s) => !s)}
                      className="h-8 gap-1.5 px-2.5 text-xs font-semibold text-muted-foreground hover:text-foreground"
                    >
                      <Layers className="h-4 w-4 text-primary" />
                      Layers
                    </Button>
                  </div>

                  {showSettings && (
                    <div className="pointer-events-auto w-64 rounded-xl border border-border bg-card/95 p-3.5 shadow-2xl backdrop-blur-md">
                      <div className="mb-2.5 flex items-center justify-between border-b border-border/50 pb-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-foreground">Map Layers</span>
                        <button
                          onClick={() => setShowSettings(false)}
                          className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                        >
                          Close
                        </button>
                      </div>
                      <div className="space-y-2.5">
                        {(
                          [
                            ["zones", "Disaster zones"],
                            ["routes", "Aid routes"],
                            ["resources", "Resource staging"],
                            ["facilities", "Shelters & hospitals"],
                            ["incidents", "Incident markers"],
                          ] as [keyof LayerToggles, string][]
                        ).map(([key, label]) => (
                          <label
                            key={key}
                            className="flex items-center justify-between text-xs font-medium text-muted-foreground"
                          >
                            {label}
                            <Switch
                              checked={layers[key]}
                              onCheckedChange={(v) =>
                                setLayers((prev) => ({ ...prev, [key]: v }))
                              }
                            />
                          </label>
                        ))}
                      </div>

                      <div className="mt-3.5 border-t border-border/50 pt-2.5 text-xs">
                        <p className="mb-2 font-bold text-foreground">Legend</p>
                        <div className="space-y-1.5">
                          <LegendRow color="bg-sky-500" label={`${derived.type.label} inundation zone`} />
                          <LegendRow color="bg-primary" label="Aid route / staging point" />
                          <LegendRow color="bg-sky-600" label="Shelter · Hospital · Warehouse" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Right Side Key Matrix & AI Recommendation Panel */}
            <aside className="w-full lg:w-96 shrink-0 h-[52vh] min-h-[460px] flex flex-col justify-between rounded-2xl border border-border/80 bg-card p-4.5 shadow-xl overflow-y-auto">
              <div>
                <div className="flex items-center justify-between border-b border-border/50 pb-2.5">
                  <div className="flex items-center gap-2 text-sm font-bold text-primary">
                    <Sparkles className="h-4.5 w-4.5" /> Key AI Decision Matrix
                  </div>
                  <span className="rounded-md bg-primary/15 px-2 py-0.5 text-xs font-bold text-primary">
                    Live EOC
                  </span>
                </div>

                <p className="mt-3 text-base font-bold leading-snug text-foreground">{derived.ai.action}</p>

                <div className="mt-3.5 space-y-2 border-t border-border/50 pt-2.5">
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Algorithm Confidence</span>
                    <span className="font-mono text-sm font-bold text-primary">{derived.ai.confidence}%</span>
                  </div>
                  <Progress value={derived.ai.confidence} className="h-2" />
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Deployment ETA</span>
                    <span className="font-mono text-sm font-bold text-foreground">{derived.ai.eta} mins</span>
                  </div>
                </div>

                <div className="mt-3.5 border-t border-border/50 pt-2.5">
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Operational Rationale</p>
                  <ul className="space-y-1.5 text-xs leading-relaxed text-muted-foreground">
                    {derived.ai.reasons.map((r) => (
                      <li key={r} className="flex gap-2 font-medium">
                        <span className="font-bold text-primary">•</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-4 border-t border-border/50 pt-3">
                <ApprovalExecutionPanel
                  threadId={activeThreadId}
                  incidentId={backendIncidents[0]?.incident_id || "inc-demo-1"}
                  allocations={activeAllocations}
                  onStateChange={refreshBackendData}
                />
              </div>
            </aside>
          </div>

          {/* Dashboard Sections Below Top Row */}
          <div className="space-y-5 px-3.5 pb-6">
            {/* Row 2: Selected Incident Details Grid */}
            <div className="panel-in rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-border/50 pb-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-primary">Selected Incident Details</p>
                  <h2 className="text-lg font-bold text-foreground mt-0.5">{detail.title}</h2>
                </div>
                <span className="rounded-lg bg-destructive/15 px-3 py-1 text-xs font-bold text-destructive uppercase">
                  {detail.severity} severity
                </span>
              </div>

              <p className="mt-3 text-xs font-medium text-muted-foreground leading-relaxed">{detail.detail}</p>

              <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4 text-xs">
                <Field label="Disaster Zone" value={derived.zone.name} />
                <Field label="Severity Rating" value={detail.severity} />
                <Field label="Footprint Overlay" value={derived.type.overlay} />
                <Field
                  label="Affected Population"
                  value={scenario.affectedPopulation.toLocaleString()}
                />
              </dl>

              {scenario.notes && (
                <div className="mt-3.5 rounded-xl bg-secondary/80 p-3 text-xs leading-relaxed text-muted-foreground border border-border/60">
                  <span className="font-bold text-foreground block mb-1">EOC Notes:</span>
                  {scenario.notes}
                </div>
              )}
            </div>

            {/* Row 3: Resource Allocation & Shelters */}
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              {/* Resource Allocation Table (2 Cols on lg) */}
              <div className="panel-in rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:col-span-2">
                <div className="flex items-center justify-between border-b border-border/50 pb-3">
                  <p className="flex items-center gap-2 text-base font-bold text-foreground">
                    <Boxes className="h-5 w-5 text-primary" /> Resource Allocation &amp; Deployment Routes
                  </p>
                  <span className="text-xs font-medium text-muted-foreground">
                    {derived.deployments.length} Active Units
                  </span>
                </div>

                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead className="text-muted-foreground border-b border-border">
                      <tr className="text-left">
                        <th className="py-2.5 font-bold">Unit Name</th>
                        <th className="py-2.5 font-bold">Origin Base</th>
                        <th className="py-2.5 font-bold">Target Zone</th>
                        <th className="py-2.5 font-bold">ETA</th>
                        <th className="py-2.5 font-bold">Deployment Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {derived.deployments.map((d) => (
                        <tr key={d.id} className="border-t border-border/40 hover:bg-muted/30 transition-colors">
                          <td className="py-3 font-bold text-foreground">
                            <span className="flex items-center gap-2">
                              <RouteIcon className="h-4 w-4 text-primary" />
                              {d.unit}
                            </span>
                          </td>
                          <td className="py-3 text-muted-foreground font-medium">{d.from}</td>
                          <td className="py-3 text-muted-foreground font-medium">{d.toZone}</td>
                          <td className="py-3 font-mono font-bold text-foreground">{d.etaMins} mins</td>
                          <td className="py-3">
                            <span
                              className={`rounded-md px-2.5 py-1 text-xs font-bold ${
                                d.status === "On site"
                                  ? "bg-emerald-500/15 text-emerald-400"
                                  : d.status === "En route"
                                    ? "bg-primary/15 text-primary"
                                    : "bg-amber-500/15 text-amber-400"
                              }`}
                            >
                              {d.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Shelters & Facilities (1 Col on lg) */}
              <div className="panel-in rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
                <div className="flex items-center justify-between border-b border-border/50 pb-3">
                  <p className="text-base font-bold text-foreground">Shelters &amp; Staging Facilities</p>
                  <span className="text-xs font-medium text-muted-foreground">{derived.facilities.length} Listed</span>
                </div>

                <ul className="mt-4 space-y-4">
                  {derived.facilities.map((f) => {
                    const pct = Math.round((f.occupied / f.capacity) * 100);
                    return (
                      <li key={f.id} className="text-xs font-medium space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground">{f.name}</span>
                          <span className="font-mono font-bold text-muted-foreground">
                            {f.occupied} / {f.capacity} ({pct}%)
                          </span>
                        </div>
                        <Progress value={pct} className="h-2" />
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>

            {/* Row 4: Live Event Timeline */}
            <div className="panel-in rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-border/50 pb-3">
                <p className="flex items-center gap-2 text-base font-bold text-foreground">
                  <Clock className="h-5 w-5 text-primary" /> Real-Time Operational Event Timeline
                </p>
                <span className="text-xs font-medium text-muted-foreground">Live Feed Updates</span>
              </div>

              <div className="mt-4">
                <ol className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {derived.timeline.map((t) => (
                    <li key={t.at} className="flex gap-3 rounded-xl border border-border/60 bg-background p-3 text-xs leading-relaxed shadow-2xs">
                      <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-primary animate-pulse" />
                      <div>
                        <span className="block font-mono font-bold text-muted-foreground mb-0.5">{formatClock(t.at)}</span>
                        <span className="font-semibold text-foreground">{t.text}</span>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  </div>
</div>
);
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "alert" | "primary" | "warning";
}) {
  const toneClass =
    tone === "alert" ? "text-destructive" : tone === "primary" ? "text-primary" : "text-amber-400";
  return (
    <div className="rounded-lg border border-border bg-secondary/80 px-3.5 py-1.5 text-center shadow-xs">
      <span className={`block font-display text-base font-bold ${toneClass}`}>{value}</span>
      <span className="block text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
        active
          ? "border-primary bg-primary/20 text-primary font-bold shadow-xs"
          : "border-border bg-secondary text-muted-foreground hover:text-foreground"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function LegendRow({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2 py-0.5 text-xs font-medium text-muted-foreground">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      {label}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-secondary/90 px-2.5 py-2">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="truncate capitalize font-bold text-foreground text-xs">{value}</dd>
    </div>
  );
}
