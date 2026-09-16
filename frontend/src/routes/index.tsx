import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Radio, ShieldAlert, ArrowRight } from "lucide-react";
import gsap from "gsap";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DEFAULT_SCENARIO,
  DISASTER_TYPES,
  RESOURCE_OPTIONS,
  SEVERITIES,
  ZONES,
  saveScenario,
  type DisasterType,
  type Severity,
} from "@/lib/scenario";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ResQAI — Start a Disaster Response Simulation" },
      {
        name: "description",
        content:
          "Enter disaster type, zone, severity, affected population and resources to launch the ResQAI emergency response command dashboard.",
      },
      { property: "og:title", content: "ResQAI — Disaster Response Simulation" },
      {
        property: "og:description",
        content:
          "Launch a live emergency operations dashboard with disaster overlays, resource routing and AI recommendations.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Home,
});

function Home() {
  const navigate = useNavigate();
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [disasterType, setDisasterType] = useState<DisasterType>(DEFAULT_SCENARIO.disasterType);
  const [zoneId, setZoneId] = useState(DEFAULT_SCENARIO.zoneId);
  const [severity, setSeverity] = useState<Severity>(DEFAULT_SCENARIO.severity);
  const [population, setPopulation] = useState(String(DEFAULT_SCENARIO.affectedPopulation));
  const [resources, setResources] = useState<string[]>(DEFAULT_SCENARIO.resources);
  const [notes, setNotes] = useState(DEFAULT_SCENARIO.notes);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".hero-line", { y: 18, opacity: 0, duration: 0.6, stagger: 0.08, ease: "power3.out" });
      if (cardRef.current) {
        gsap.from(cardRef.current, { y: 28, opacity: 0, duration: 0.7, delay: 0.15, ease: "power3.out" });
      }
    });
    return () => ctx.revert();
  }, []);

  function toggleResource(name: string) {
    setResources((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name],
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    saveScenario({
      disasterType,
      zoneId,
      severity,
      affectedPopulation: Number(population) || 0,
      resources,
      notes,
      startedAt: Date.now(),
    });
    void navigate({ to: "/dashboard" });
  }

  return (
    <main className="grid-lines min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-12 lg:flex-row lg:items-center lg:py-20">
        <section className="flex-1">
          <div className="hero-line inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="live-dot h-2 w-2 rounded-full bg-destructive" />
            Emergency Operations Centre
          </div>
          <h1 className="hero-line mt-6 text-4xl font-bold leading-tight md:text-5xl">
            ResQAI
            <span className="block text-primary">Disaster Response System</span>
          </h1>
          <p className="hero-line mt-5 max-w-md text-sm leading-relaxed text-muted-foreground md:text-base">
            Define the incoming situation, then launch the command dashboard: live disaster
            overlays on satellite and 3D maps, resource routing, shelters and AI-prioritised
            response actions.
          </p>
          <ul className="hero-line mt-8 grid max-w-md gap-3 text-sm text-muted-foreground">
            {[
              "Accurate overlays per disaster type — flood, fire, quake, cyclone, rain, landslide",
              "Resource routes with assigned units, receiving zone and ETA",
              "Satellite and 3D map modes with terrain and buildings",
            ].map((t) => (
              <li key={t} className="flex gap-2">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </section>

        <div ref={cardRef} className="w-full flex-1 rounded-xl border border-border bg-card p-6 shadow-2xl md:p-8">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Radio className="h-4 w-4 text-primary" />
            Incident Intake
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Prefilled with the current live feed. Adjust anything and start the simulation.
          </p>

          <form onSubmit={submit} className="mt-6 space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Disaster type</Label>
                <Select
                  value={disasterType}
                  onValueChange={(v) => setDisasterType(v as DisasterType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DISASTER_TYPES.map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Location / zone</Label>
                <Select value={zoneId} onValueChange={setZoneId}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ZONES.map((z) => (
                      <SelectItem key={z.id} value={z.id}>
                        {z.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Severity level</Label>
                <Select value={severity} onValueChange={(v) => setSeverity(v as Severity)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SEVERITIES.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="population">Affected population</Label>
                <Input
                  id="population"
                  inputMode="numeric"
                  value={population}
                  onChange={(e) => setPopulation(e.target.value.replace(/[^\d]/g, ""))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Required resources</Label>
              <div className="flex flex-wrap gap-2">
                {RESOURCE_OPTIONS.map((r) => {
                  const active = resources.includes(r);
                  return (
                    <button
                      key={r}
                      type="button"
                      onClick={() => toggleResource(r)}
                      className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                        active
                          ? "border-primary bg-primary/15 text-primary font-medium"
                          : "border-border bg-secondary text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {r}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes / description (optional)</Label>
              <Textarea
                id="notes"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Ground reports, hazards, access constraints…"
              />
            </div>

            <Button type="submit" size="lg" className="w-full">
              Start Simulation
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </main>
  );
}
