import { curvedPath, destination, hashString, mulberry32, type LngLat } from "./geo";
import { getLocation } from "./locations";
import type {
  Deployment,
  DisasterType,
  Facility,
  FeedEvent,
  Incident,
  Recommendation,
  Scenario,
  ScenarioInput,
  Severity,
  Zone,
} from "./types";

export const DISASTER_LABELS: Record<DisasterType, string> = {
  flood: "Urban Flooding",
  fire: "Wildfire / Fire",
  earthquake: "Earthquake",
  rain: "Heavy Rainfall",
  cyclone: "Cyclone",
};

export const SEVERITY_ORDER: Severity[] = ["low", "moderate", "high", "critical"];

export const SEVERITY_COLOR: Record<Severity, string> = {
  low: "#38bdf8",
  moderate: "#fbbf24",
  high: "#fb923c",
  critical: "#f43f5e",
};

export const RESOURCE_OPTIONS = [
  "Rescue Boats",
  "Medical Teams",
  "Fire Tenders",
  "Food & Water",
  "Evacuation Buses",
  "Drones",
  "Heavy Machinery",
  "Power Restoration",
];

export const DEFAULT_INPUT: ScenarioInput = {
  disasterType: "flood",
  locationKey: "mumbai",
  severity: "high",
  population: 18200,
  resources: ["Rescue Boats", "Medical Teams", "Food & Water"],
  notes: "",
};

const sevWeight: Record<Severity, number> = { low: 0.55, moderate: 0.8, high: 1, critical: 1.3 };

function clockFrom(offsetMin: number) {
  const base = new Date();
  base.setMinutes(base.getMinutes() - offsetMin);
  return base.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true });
}

export function buildScenario(input: ScenarioInput): Scenario {
  const loc = getLocation(input.locationKey);
  const rnd = mulberry32(hashString(input.locationKey + input.disasterType + input.severity));
  const w = sevWeight[input.severity];

  const zoneCount = input.disasterType === "earthquake" ? 4 : 5;
  const zones: Zone[] = Array.from({ length: zoneCount }).map((_, i) => {
    const bearing = (i / zoneCount) * 360 + rnd() * 40;
    const dist = 1.6 + rnd() * 4.2;
    const center = destination(loc.center, dist, bearing);
    const sev: Severity =
      i === 0 ? (w >= 1 ? "critical" : "high") : SEVERITY_ORDER[Math.min(3, Math.floor(rnd() * 3) + (w >= 1 ? 1 : 0))]!;
    return {
      id: `zone-${i}`,
      name: loc.zones[i % loc.zones.length]!,
      severity: sev,
      waterLevel: input.disasterType === "flood" ? +(0.8 + rnd() * 2 * w).toFixed(1) : undefined,
      affected: Math.round((input.population / zoneCount) * (0.6 + rnd() * 0.9)),
      center,
      radiusKm: +(0.8 + rnd() * 1.6 * w).toFixed(2),
    };
  });

  const criticalZones = zones.filter((z) => z.severity === "critical" || z.severity === "high");

  const incidentTemplates: Record<DisasterType, string[]> = {
    flood: ["Severe waterlogging", "Stranded residents", "Submerged underpass", "Drainage overflow"],
    fire: ["Active fire front", "Structure ablaze", "Smoke hazard", "Gas line risk"],
    earthquake: ["Collapsed structure", "Gas leak reported", "Road fissure", "Trapped residents"],
    rain: ["Flash flood warning", "Tree fall blockage", "Waterlogged junction", "Power line down"],
    cyclone: ["Storm surge risk", "Roof damage cluster", "Coastal evacuation", "Power grid failure"],
  };

  const incidents: Incident[] = zones.slice(0, 5).map((z, i) => ({
    id: `inc-${i}`,
    title: incidentTemplates[input.disasterType][i % 4]!,
    zone: z.name,
    severity: z.severity,
    detail:
      input.disasterType === "flood"
        ? `Water level ${z.waterLevel} m · ${z.affected.toLocaleString("en-IN")} affected`
        : `${z.affected.toLocaleString("en-IN")} people affected in sector`,
    center: destination(z.center, z.radiusKm * 0.45, rnd() * 360),
  }));

  const facilityKinds: Facility["kind"][] = ["shelter", "hospital", "warehouse", "shelter", "shelter", "hospital"];
  const facilities: Facility[] = facilityKinds.map((kind, i) => {
    const center = destination(loc.center, 2.2 + rnd() * 5.5, rnd() * 360);
    const capacity = kind === "shelter" ? 300 + Math.round(rnd() * 500) : kind === "hospital" ? 180 : 900;
    return {
      id: `fac-${i}`,
      name:
        kind === "shelter"
          ? `${loc.zones[(i + 1) % loc.zones.length]!} Relief Center`
          : kind === "hospital"
            ? `${loc.zones[(i + 2) % loc.zones.length]!} General Hospital`
            : `${loc.zones[(i + 3) % loc.zones.length]!} Supply Depot`,
      kind,
      capacity,
      occupied: Math.round(capacity * (0.25 + rnd() * 0.55)),
      center,
    };
  });

  const resources = input.resources.length ? input.resources : DEFAULT_INPUT.resources;
  const deployments: Deployment[] = resources.slice(0, 5).map((resource, i) => {
    const target = criticalZones[i % Math.max(1, criticalZones.length)] ?? zones[0]!;
    const origin = facilities[(i + 2) % facilities.length]!;
    return {
      id: `dep-${i}`,
      unit: `Team ${["Alpha", "Bravo", "Charlie", "Delta", "Echo"][i] ?? "Unit"}`,
      resource,
      toZone: target.name,
      etaMin: 4 + Math.round(rnd() * 22),
      status: i === 0 ? "on-site" : i === 1 ? "staging" : "en-route",
      path: curvedPath(origin.center as LngLat, target.center as LngLat, 0.14 + rnd() * 0.12),
    };
  });

  const feed: FeedEvent[] = [
    { kind: "alert" as const, text: `${DISASTER_LABELS[input.disasterType]} escalating in ${zones[0]!.name}` },
    { kind: "resource" as const, text: `${deployments[0]?.unit ?? "Team Alpha"} dispatched with ${resources[0]}` },
    { kind: "shelter" as const, text: `${facilities[0]!.name} activated · capacity ${facilities[0]!.capacity}` },
    { kind: "weather" as const, text: `Conditions worsening around ${zones[1]?.name ?? loc.label}` },
    { kind: "ai" as const, text: `AI flagged ${criticalZones.length} priority zones for immediate response` },
    { kind: "resource" as const, text: `Supply corridor opened from ${facilities[2]!.name}` },
    { kind: "alert" as const, text: `Road access restricted near ${zones[2]?.name ?? loc.label}` },
    { kind: "shelter" as const, text: `${facilities[3]!.name} at ${Math.round((facilities[3]!.occupied / facilities[3]!.capacity) * 100)}% occupancy` },
  ].map((e, i) => ({ ...e, id: `evt-${i}`, time: clockFrom(i * 3 + 1) }));

  const recommendations: Recommendation[] = [
    {
      id: "rec-0",
      title: `Deploy 2 ${resources[0]?.toLowerCase() ?? "rescue units"} to ${zones[0]!.name}`,
      confidence: Math.min(97, 78 + Math.round(w * 12)),
      etaMin: deployments[0]?.etaMin ?? 12,
      reason: `Highest concentration of affected population (${zones[0]!.affected.toLocaleString("en-IN")}). Nearest staging point is ${facilities[2]!.name}.`,
    },
    {
      id: "rec-1",
      title: `Open overflow shelter at ${facilities[1]!.name}`,
      confidence: 71 + Math.round(rnd() * 15),
      etaMin: 25,
      reason: `Primary shelters projected to exceed capacity within 2 hours at current intake rate.`,
    },
    {
      id: "rec-2",
      title: `Reroute aid corridor around ${zones[2]?.name ?? loc.label}`,
      confidence: 66 + Math.round(rnd() * 18),
      etaMin: 9,
      reason: `Main access route degraded; alternate corridor reduces transit by an estimated 11 minutes.`,
    },
  ];

  return {
    input,
    title: `${loc.label} ${DISASTER_LABELS[input.disasterType]}`,
    subtitle: `${loc.region} · ${input.severity.toUpperCase()} severity`,
    center: loc.center,
    zoom: loc.zoom,
    zones,
    incidents,
    facilities,
    deployments,
    priority: criticalZones,
    feed,
    recommendations,
    stats: {
      incidents: incidents.length,
      affected: input.population,
      criticalZones: criticalZones.length,
      resources: resources.length * 7,
    },
  };
}
