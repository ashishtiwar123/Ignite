import type { LayerSpecification } from "mapbox-gl";
import type { FeatureCollection } from "geojson";

export type DisasterType = "flood" | "fire" | "earthquake" | "rain" | "cyclone" | "landslide";

export type Severity = "low" | "moderate" | "high" | "critical";

export interface ScenarioInput {
  disasterType: DisasterType;
  locationKey: string;
  severity: Severity;
  population: number;
  resources: string[];
  notes: string;
}

export interface Zone {
  id: string;
  name: string;
  severity: Severity;
  waterLevel?: number | undefined;
  affected: number;
  center: [number, number];
  radiusKm: number;
}

export interface Incident {
  id: string;
  title: string;
  zone: string;
  severity: Severity;
  detail: string;
  center: [number, number];
}

export interface Facility {
  id: string;
  name: string;
  kind: "shelter" | "hospital" | "warehouse";
  capacity: number;
  occupied: number;
  center: [number, number];
}

export interface Deployment {
  id: string;
  unit: string;
  resource: string;
  toZone: string;
  etaMin: number;
  status: "en-route" | "on-site" | "staging";
  path: [number, number][];
}

export interface FeedEvent {
  id: string;
  time: string;
  kind: "alert" | "resource" | "shelter" | "weather" | "ai";
  text: string;
}

export interface Recommendation {
  id: string;
  title: string;
  confidence: number;
  etaMin: number;
  reason: string;
}

export interface Scenario {
  input: ScenarioInput;
  title: string;
  subtitle: string;
  center: [number, number];
  zoom: number;
  zones: Zone[];
  incidents: Incident[];
  facilities: Facility[];
  deployments: Deployment[];
  priority: Zone[];
  feed: FeedEvent[];
  recommendations: Recommendation[];
  stats: { incidents: number; affected: number; criticalZones: number; resources: number };
}

/** Contract every map layer module implements. */
export interface MapLayerModule {
  id: string;
  label: string;
  color: string;
  defaultVisible: boolean;
  /** Return the sources and mapbox layer specs this layer owns. */
  build(scenario: Scenario): {
    sources: Record<string, FeatureCollection>;
    layers: LayerSpecification[];
  };
}
