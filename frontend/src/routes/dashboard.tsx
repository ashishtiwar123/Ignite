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
  Gauge,
  LayoutDashboard,
  Layers,
  Mountain,
  Route as RouteIcon,
  Satellite,
  Settings,
  Sparkles,
  Truck,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { LayerToggles, MapMode } from "@/components/dr/DisasterMap";
import {
  DISASTER_TYPES,
  aiRecommendation,
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
  { id: "simulation", label: "Simulation", icon: Gauge },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
];

function Dashboard() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mode, setMode] = useState<MapMode>("3d");
  const [activeNav, setActiveNav] = useState("dashboard");
  const [showSettings, setShowSettings] = useState(true);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [layers, setLayers] = useState<LayerToggles>({
    zones: true,
    routes: true,
    resources: true,
    facilities: true,
    incidents: true,
    priority: true,
  });
  const shellRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setScenario(loadScenario());
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
      <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-card px-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-md bg-primary/15 text-primary">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="hidden leading-tight sm:block">
            <span className="block text-sm font-bold">ResQAI</span>
            <span className="block text-[10px] text-muted-foreground">
              Disaster Response System
            </span>
          </span>
        </Link>
        <span className="flex items-center gap-2 rounded-md bg-destructive/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-destructive">
          <span className="live-dot h-1.5 w-1.5 rounded-full bg-destructive" /> Live
        </span>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-semibold">
            {derived.zone.name} · {derived.type.label}
          </h1>
          <p className="truncate text-[11px] text-muted-foreground">
            {derived.type.overlay} · severity {scenario.severity}
          </p>
        </div>
        <div className="ml-auto hidden items-center gap-2 lg:flex">
          <Stat label="Active Incidents" value={String(derived.incidents.length)} tone="alert" />
          <Stat
            label="People Affected"
            value={scenario.affectedPopulation.toLocaleString()}
            tone="primary"
          />
          <Stat label="Units Deployed" value={String(derived.deployments.length)} tone="warning" />
        </div>
        <div className="text-right text-[11px] leading-tight text-muted-foreground">
          <span className="block font-mono text-sm text-foreground">
            {formatClock(scenario.startedAt)}
          </span>
          EOC Mumbai
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* sidebar */}
        <aside
          className={`relative flex shrink-0 flex-col border-r border-border bg-card transition-[width] duration-300 ${
            collapsed ? "w-14" : "w-56"
          }`}
        >
          <nav className="flex-1 space-y-1 p-2">
            {NAV.map((item) => {
              const active = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  title={item.label}
                  className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                    active
                      ? "bg-primary/15 text-primary font-medium"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </nav>
          {!collapsed && (
            <div className="border-t border-border p-4 text-[11px] text-muted-foreground">
              <p className="font-display text-sm font-semibold text-foreground">India</p>
              Disaster Ready · Stronger Together
            </div>
          )}
          <Button
            variant="secondary"
            size="icon"
            onClick={() => setCollapsed((c) => !c)}
            className="absolute -right-3 top-3 h-6 w-6 rounded-full border border-border"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronLeft className="h-3.5 w-3.5" />
            )}
          </Button>
        </aside>

        {/* center + right */}
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            {/* map */}
            <section className="relative min-w-0 flex-1">
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
                  />
                </Suspense>
              </ClientOnly>

              {/* map settings overlay */}
              <div className="pointer-events-none absolute inset-0 p-3">
                <div className="pointer-events-auto flex w-64 flex-col gap-2">
                  <div className="panel-in rounded-lg border border-border bg-card/90 p-3 shadow-lg backdrop-blur-md">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-xs font-semibold">
                        <Layers className="h-3.5 w-3.5 text-primary" /> Map Settings
                      </span>
                      <button
                        onClick={() => setShowSettings((s) => !s)}
                        className="text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        {showSettings ? "Hide" : "Show"}
                      </button>
                    </div>

                    {showSettings && (
                      <>
                        <div className="mt-3 grid grid-cols-2 gap-2">
                          <ModeButton
                            active={mode === "satellite"}
                            onClick={() => setMode("satellite")}
                            icon={<Satellite className="h-3.5 w-3.5" />}
                            label="Satellite"
                          />
                          <ModeButton
                            active={mode === "3d"}
                            onClick={() => setMode("3d")}
                            icon={<Mountain className="h-3.5 w-3.5" />}
                            label="3D View"
                          />
                        </div>
                        <div className="mt-3 space-y-2">
                          {(
                            [
                              ["zones", "Disaster zones"],
                              ["priority", "AI priority regions"],
                              ["routes", "Aid routes"],
                              ["resources", "Resource staging"],
                              ["facilities", "Shelters & hospitals"],
                              ["incidents", "Incident markers"],
                            ] as [keyof LayerToggles, string][]
                          ).map(([key, label]) => (
                            <label
                              key={key}
                              className="flex items-center justify-between text-[11px] text-muted-foreground"
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
                      </>
                    )}
                  </div>

                  <div className="panel-in rounded-lg border border-border bg-card/90 p-3 text-[11px] shadow-lg backdrop-blur-md">
                    <p className="mb-2 text-xs font-semibold">Legend</p>
                    <LegendRow color="bg-destructive" label={`${derived.type.label} impact zone`} />
                    <LegendRow color="bg-chart-3" label="AI priority region" />
                    <LegendRow color="bg-primary" label="Aid route / staging point" />
                    <LegendRow color="bg-chart-2" label="Shelter · Hospital · Warehouse" />
                  </div>
                </div>
              </div>
            </section>

            {/* right panel */}
            <aside className="hidden w-80 shrink-0 border-l border-border bg-card xl:block">
              <ScrollArea className="h-full">
                <div className="space-y-3 p-3">
                  <div className="panel-in rounded-lg border border-border bg-background p-3 shadow-sm">
                    <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                      <Sparkles className="h-3.5 w-3.5" /> AI Recommendation
                    </div>
                    <p className="mt-2 text-sm font-medium leading-snug">{derived.ai.action}</p>
                    <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>Confidence</span>
                      <span className="font-mono text-primary font-semibold">{derived.ai.confidence}%</span>
                    </div>
                    <Progress value={derived.ai.confidence} className="mt-1.5 h-1.5" />
                    <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>ETA</span>
                      <span className="font-mono text-foreground">{derived.ai.eta} mins</span>
                    </div>
                    <ul className="mt-3 space-y-1 text-[11px] text-muted-foreground">
                      {derived.ai.reasons.map((r) => (
                        <li key={r} className="flex gap-1.5">
                          <span className="text-primary">•</span>
                          {r}
                        </li>
                      ))}
                    </ul>
                    <Button className="mt-3 w-full" size="sm">
                      Approve &amp; Dispatch
                    </Button>
                    <Button variant="outline" className="mt-2 w-full" size="sm">
                      View Alternatives
                    </Button>
                  </div>

                  <div className="panel-in rounded-lg border border-border bg-background p-3 shadow-sm">
                    <p className="text-xs font-semibold">Incident Details</p>
                    <p className="mt-2 text-sm font-medium">{detail.title}</p>
                    <p className="text-[11px] text-muted-foreground">{detail.detail}</p>
                    <dl className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                      <Field label="Zone" value={derived.zone.name} />
                      <Field label="Severity" value={detail.severity} />
                      <Field label="Overlay" value={derived.type.overlay} />
                      <Field
                        label="Population"
                        value={scenario.affectedPopulation.toLocaleString()}
                      />
                    </dl>
                    {scenario.notes && (
                      <p className="mt-3 rounded-md bg-secondary p-2 text-[11px] text-muted-foreground">
                        {scenario.notes}
                      </p>
                    )}
                    <p className="mt-2 text-[10px] text-muted-foreground">
                      Tip: click any incident marker on the map to inspect it here.
                    </p>
                  </div>

                  <div className="panel-in rounded-lg border border-border bg-background p-3 shadow-sm">
                    <p className="text-xs font-semibold">Live Updates</p>
                    <ul className="mt-2 space-y-2">
                      {derived.timeline.slice(0, 5).map((t) => (
                        <li key={t.at} className="flex gap-2 text-[11px]">
                          <span className="font-mono text-muted-foreground">
                            {formatClock(t.at)}
                          </span>
                          <span className="text-foreground/90">{t.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="panel-in rounded-lg border border-border bg-background p-3 shadow-sm">
                    <p className="text-xs font-semibold">Shelters &amp; Facilities</p>
                    <ul className="mt-2 space-y-2">
                      {derived.facilities.map((f) => (
                        <li key={f.id} className="text-[11px]">
                          <div className="flex justify-between">
                            <span className="text-foreground">{f.name}</span>
                            <span className="font-mono text-muted-foreground">
                              {f.occupied}/{f.capacity}
                            </span>
                          </div>
                          <Progress
                            value={(f.occupied / f.capacity) * 100}
                            className="mt-1 h-1"
                          />
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </ScrollArea>
            </aside>
          </div>

          {/* bottom feed */}
          <section className="h-52 shrink-0 border-t border-border bg-card">
            <div className="grid h-full grid-cols-1 divide-x divide-border lg:grid-cols-2">
              <div className="min-h-0 p-3">
                <p className="flex items-center gap-2 text-xs font-semibold">
                  <Boxes className="h-3.5 w-3.5 text-primary" /> Resource Allocation
                </p>
                <ScrollArea className="mt-2 h-[calc(100%-1.75rem)]">
                  <table className="w-full text-[11px]">
                    <thead className="text-muted-foreground">
                      <tr className="text-left">
                        <th className="pb-1 font-medium">Unit</th>
                        <th className="pb-1 font-medium">Route from</th>
                        <th className="pb-1 font-medium">Receiving zone</th>
                        <th className="pb-1 font-medium">ETA</th>
                        <th className="pb-1 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {derived.deployments.map((d) => (
                        <tr key={d.id} className="border-t border-border/60">
                          <td className="py-1.5">
                            <span className="flex items-center gap-1.5">
                              <RouteIcon className="h-3 w-3 text-primary" />
                              {d.unit}
                            </span>
                          </td>
                          <td className="py-1.5 text-muted-foreground">{d.from}</td>
                          <td className="py-1.5 text-muted-foreground">{d.toZone}</td>
                          <td className="py-1.5 font-mono">{d.etaMins}m</td>
                          <td className="py-1.5">
                            <span
                              className={`rounded px-1.5 py-0.5 font-medium ${
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
                </ScrollArea>
              </div>

              <div className="min-h-0 p-3">
                <p className="flex items-center gap-2 text-xs font-semibold">
                  <Clock className="h-3.5 w-3.5 text-primary" /> Event Timeline
                </p>
                <ScrollArea className="mt-2 h-[calc(100%-1.75rem)]">
                  <ol className="space-y-2 pr-2">
                    {derived.timeline.map((t) => (
                      <li key={t.at} className="flex gap-2 text-[11px]">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                        <span className="font-mono text-muted-foreground">{formatClock(t.at)}</span>
                        <span>{t.text}</span>
                      </li>
                    ))}
                  </ol>
                </ScrollArea>
              </div>
            </div>
          </section>
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
    <div className="rounded-md border border-border bg-secondary px-3 py-1.5 text-center">
      <span className={`block font-display text-sm font-bold ${toneClass}`}>{value}</span>
      <span className="block text-[10px] text-muted-foreground">{label}</span>
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
      className={`flex items-center justify-center gap-1.5 rounded-md border px-2 py-1.5 text-[11px] transition-colors ${
        active
          ? "border-primary bg-primary/15 text-primary font-medium"
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
    <div className="flex items-center gap-2 py-0.5 text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-secondary px-2 py-1.5">
      <dt className="text-[10px] text-muted-foreground">{label}</dt>
      <dd className="truncate capitalize text-foreground">{value}</dd>
    </div>
  );
}
