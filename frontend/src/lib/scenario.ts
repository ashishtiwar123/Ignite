export type DisasterType =
  | "flood"
  | "fire"
  | "earthquake"
  | "cyclone"
  | "heavy_rain";

export type Severity = "low" | "moderate" | "high" | "critical";

export interface Scenario {
  disasterType: DisasterType;
  zoneId: string;
  severity: Severity;
  affectedPopulation: number;
  resources: string[];
  notes: string;
  startedAt: number;
}

export interface Zone {
  id: string;
  name: string;
  center: [number, number];
}

export const ZONES: Zone[] = [
  { id: "kurla-west", name: "Kurla West", center: [72.8792, 19.0701] },
  { id: "lower-parel", name: "Lower Parel", center: [72.8303, 18.9977] },
  { id: "bandra-east", name: "Bandra East", center: [72.8465, 19.0607] },
  { id: "sion", name: "Sion", center: [72.8624, 19.0392] },
  { id: "bkc", name: "Bandra Kurla Complex", center: [72.8677, 19.0662] },
  { id: "dadar", name: "Dadar", center: [72.8446, 19.0186] },
];

export const DISASTER_TYPES: { id: DisasterType; label: string; overlay: string }[] = [
  { id: "flood", label: "Flood", overlay: "Water inundation overlay" },
  { id: "fire", label: "Fire / Wildfire", overlay: "Fire & heat zone" },
  { id: "earthquake", label: "Earthquake", overlay: "Epicenter + impact rings" },
  { id: "cyclone", label: "Cyclone", overlay: "Forecast track & storm cloud" },
  { id: "heavy_rain", label: "Heavy Rainfall", overlay: "Rainfall radar overlay" },
];

export const SEVERITIES: { id: Severity; label: string }[] = [
  { id: "low", label: "Low" },
  { id: "moderate", label: "Moderate" },
  { id: "high", label: "High" },
  { id: "critical", label: "Critical" },
];

export const RESOURCE_OPTIONS = [
  "Rescue Boats",
  "Fire Trucks",
  "Ambulances",
  "Medical Teams",
  "Relief Supplies",
  "Heavy Machinery",
  "Drone Survey",
  "Evacuation Buses",
];

export const DEFAULT_SCENARIO: Scenario = {
  disasterType: "flood",
  zoneId: "kurla-west",
  severity: "high",
  affectedPopulation: 1200,
  resources: ["Rescue Boats", "Medical Teams", "Relief Supplies"],
  notes: "Water level rising at 2.4 m. 400+ people stranded in low-lying pockets.",
  startedAt: Date.now(),
};

const KEY = "resqai.scenario";

export function saveScenario(s: Scenario) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, JSON.stringify(s));
}

export function loadScenario(): Scenario {
  if (typeof window === "undefined") return DEFAULT_SCENARIO;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return DEFAULT_SCENARIO;
    return { ...DEFAULT_SCENARIO, ...(JSON.parse(raw) as Partial<Scenario>) };
  } catch {
    return DEFAULT_SCENARIO;
  }
}

export function zoneOf(scenario: Scenario): Zone {
  return ZONES.find((z) => z.id === scenario.zoneId) ?? ZONES[0]!;
}

export const SEVERITY_RADIUS: Record<Severity, number> = {
  low: 0.8,
  moderate: 1.3,
  high: 2,
  critical: 3,
};

export const DISASTER_COLOR: Record<DisasterType, string> = {
  flood: "#38bdf8",
  fire: "#fb7185",
  earthquake: "#f97316",
  cyclone: "#a78bfa",
  heavy_rain: "#22d3ee",
};

/* ---------- geo helpers ---------- */

export function circlePolygon(
  center: [number, number],
  radiusKm: number,
  steps = 64,
): [number, number][] {
  const coords: [number, number][] = [];
  const latR = radiusKm / 110.574;
  const lngR = radiusKm / (111.32 * Math.cos((center[1] * Math.PI) / 180));
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    coords.push([center[0] + lngR * Math.cos(t), center[1] + latR * Math.sin(t)]);
  }
  return coords;
}

export function blobPolygon(
  center: [number, number],
  radiusKm: number,
  seed = 1,
  steps = 72,
): [number, number][] {
  const coords: [number, number][] = [];
  const latR = radiusKm / 110.574;
  const lngR = radiusKm / (111.32 * Math.cos((center[1] * Math.PI) / 180));
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    const w =
      0.78 +
      0.16 * Math.sin(t * 3 + seed) +
      0.1 * Math.sin(t * 5 + seed * 2.3) +
      0.06 * Math.cos(t * 7 + seed * 1.7);
    coords.push([center[0] + lngR * w * Math.cos(t), center[1] + latR * w * Math.sin(t)]);
  }
  return coords;
}

export function offset(
  center: [number, number],
  km: number,
  bearingDeg: number,
): [number, number] {
  const rad = (bearingDeg * Math.PI) / 180;
  const dLat = (km * Math.cos(rad)) / 110.574;
  const dLng = (km * Math.sin(rad)) / (111.32 * Math.cos((center[1] * Math.PI) / 180));
  return [center[0] + dLng, center[1] + dLat];
}

/* ---------- derived operational data ---------- */

export interface Facility {
  id: string;
  name: string;
  kind: "shelter" | "hospital" | "warehouse";
  coord: [number, number];
  capacity: number;
  occupied: number;
}

export interface Deployment {
  id: string;
  resource: string;
  unit: string;
  from: string;
  toZone: string;
  etaMins: number;
  status: "En route" | "On site" | "Staging";
  path: [number, number][];
  color: string;
}

const FACILITY_LAYOUT: {
  kind: Facility["kind"];
  name: string;
  km: number;
  bearing: number;
  capacity: number;
}[] = [
  { kind: "shelter", name: "Community Shelter A", km: 1.6, bearing: 40, capacity: 500 },
  { kind: "shelter", name: "Municipal School Shelter", km: 2.1, bearing: 200, capacity: 380 },
  { kind: "hospital", name: "City General Hospital", km: 2.6, bearing: 300, capacity: 220 },
  { kind: "hospital", name: "Trauma Care Centre", km: 3.4, bearing: 115, capacity: 140 },
  { kind: "warehouse", name: "Relief Supply Depot", km: 3.9, bearing: 245, capacity: 900 },
];

export function facilitiesFor(scenario: Scenario): Facility[] {
  const c = zoneOf(scenario).center;
  return FACILITY_LAYOUT.map((f, i) => ({
    id: `fac-${i}`,
    name: f.name,
    kind: f.kind,
    coord: offset(c, f.km, f.bearing),
    capacity: f.capacity,
    occupied: Math.round(f.capacity * (0.35 + 0.12 * ((i % 4) + 1))),
  }));
}

const UNIT_NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"];
const DEPOTS = ["Sion Depot", "Central Command", "Andheri Base", "Chembur Depot"];

export function deploymentsFor(scenario: Scenario): Deployment[] {
  const c = zoneOf(scenario).center;
  const base = scenario.resources.length ? scenario.resources : DEFAULT_SCENARIO.resources;
  return base.slice(0, 6).map((resource, i) => {
    const bearing = 30 + i * 61;
    const km = 4.2 + i * 0.9;
    const start = offset(c, km, bearing);
    const mid1 = offset(c, km * 0.66, bearing + 16);
    const mid2 = offset(c, km * 0.32, bearing - 12);
    return {
      id: `dep-${i}`,
      resource,
      unit: `${resource.split(" ")[0]!} Team ${UNIT_NAMES[i]!}`,
      from: DEPOTS[i % DEPOTS.length]!,
      toZone: zoneOf(scenario).name,
      etaMins: 4 + i * 3,
      status: i === 0 ? "On site" : i % 3 === 2 ? "Staging" : "En route",
      path: [start, mid1, mid2, c],
      color: i % 2 === 0 ? "#38bdf8" : "#fb7185",
    };
  });
}

export interface Incident {
  id: string;
  title: string;
  detail: string;
  coord: [number, number];
  severity: Severity;
}

export function incidentsFor(scenario: Scenario): Incident[] {
  const c = zoneOf(scenario).center;
  const t = DISASTER_TYPES.find((d) => d.id === scenario.disasterType)!;
  return [
    {
      id: "inc-1",
      title: `${t.label} — primary impact`,
      detail: `${zoneOf(scenario).name} · ${scenario.affectedPopulation.toLocaleString()} people affected`,
      coord: c,
      severity: scenario.severity,
    },
    {
      id: "inc-2",
      title: "Stranded residents reported",
      detail: "Ground team requesting additional transport",
      coord: offset(c, 1.1, 65),
      severity: "high",
    },
    {
      id: "inc-3",
      title: "Access route obstructed",
      detail: "Alternate corridor activated for relief convoy",
      coord: offset(c, 1.7, 210),
      severity: "moderate",
    },
    {
      id: "inc-4",
      title: "Power infrastructure at risk",
      detail: "Substation isolated as a precaution",
      coord: offset(c, 2.4, 320),
      severity: "moderate",
    },
  ];
}

export function timelineFor(scenario: Scenario) {
  const zone = zoneOf(scenario).name;
  const t = DISASTER_TYPES.find((d) => d.id === scenario.disasterType)!.label;
  const start = scenario.startedAt;
  const step = 4 * 60 * 1000;
  const rows: { at: number; kind: string; text: string }[] = [
    { at: start, kind: "alert", text: `${t} reported in ${zone}` },
    { at: start + step, kind: "ai", text: "AI priority zones computed from severity & population" },
    { at: start + step * 2, kind: "resource", text: `${scenario.resources.length || 3} resource types assigned` },
    { at: start + step * 3, kind: "route", text: "Fastest access corridor selected" },
    { at: start + step * 4, kind: "shelter", text: "Shelters and hospitals placed on standby" },
    { at: start + step * 5, kind: "update", text: "First response unit on site" },
  ];
  return rows.reverse();
}

export function aiRecommendation(scenario: Scenario) {
  const zone = zoneOf(scenario).name;
  const primary = (scenario.resources[0] ?? "Rescue Teams").toLowerCase();
  const confidence =
    scenario.severity === "critical"
      ? 96
      : scenario.severity === "high"
        ? 92
        : scenario.severity === "moderate"
          ? 84
          : 76;
  return {
    action: `Deploy 2 ${primary} units to ${zone}`,
    confidence,
    eta: scenario.severity === "critical" ? 8 : 12,
    reasons: [
      `${scenario.affectedPopulation.toLocaleString()} people inside the impact footprint`,
      `Severity classified as ${scenario.severity}`,
      "Nearest staging depot has capacity available",
      "Access route currently passable",
    ],
  };
}

export function formatClock(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
