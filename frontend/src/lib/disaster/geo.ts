import type { Feature, FeatureCollection, Geometry } from "geojson";

export type LngLat = [number, number];

export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hashString(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

const R = 6371;

/** Move from a point by distance (km) along a compass bearing (degrees). */
export function destination(origin: LngLat, km: number, bearingDeg: number): LngLat {
  const br = (bearingDeg * Math.PI) / 180;
  const lat1 = (origin[1] * Math.PI) / 180;
  const lng1 = (origin[0] * Math.PI) / 180;
  const dr = km / R;
  const lat2 = Math.asin(Math.sin(lat1) * Math.cos(dr) + Math.cos(lat1) * Math.sin(dr) * Math.cos(br));
  const lng2 =
    lng1 +
    Math.atan2(Math.sin(br) * Math.sin(dr) * Math.cos(lat1), Math.cos(dr) - Math.sin(lat1) * Math.sin(lat2));
  return [(lng2 * 180) / Math.PI, (lat2 * 180) / Math.PI];
}

/** Perfect circle polygon ring. */
export function circleRing(center: LngLat, km: number, steps = 72): LngLat[] {
  const ring: LngLat[] = [];
  for (let i = 0; i <= steps; i++) ring.push(destination(center, km, (i / steps) * 360));
  return ring;
}

/** Organic, non-circular polygon ring — used for flood / fire / debris footprints. */
export function blobRing(center: LngLat, km: number, seed: number, wobble = 0.38, steps = 56): LngLat[] {
  const rnd = mulberry32(seed);
  const harmonics = [
    { amp: rnd() * wobble, phase: rnd() * Math.PI * 2, freq: 2 },
    { amp: rnd() * wobble * 0.6, phase: rnd() * Math.PI * 2, freq: 3 },
    { amp: rnd() * wobble * 0.35, phase: rnd() * Math.PI * 2, freq: 5 },
  ];
  const ring: LngLat[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    let r = 1;
    for (const h of harmonics) r += h.amp * Math.sin(h.freq * t + h.phase);
    ring.push(destination(center, km * Math.max(0.45, r), (t * 180) / Math.PI));
  }
  return ring;
}

export function polygon(ring: LngLat[], props: Record<string, unknown> = {}): Feature {
  return { type: "Feature", properties: props, geometry: { type: "Polygon", coordinates: [ring] } };
}

export function line(coords: LngLat[], props: Record<string, unknown> = {}): Feature {
  return { type: "Feature", properties: props, geometry: { type: "LineString", coordinates: coords } };
}

export function point(c: LngLat, props: Record<string, unknown> = {}): Feature {
  return { type: "Feature", properties: props, geometry: { type: "Point", coordinates: c } };
}

export function fc(features: Feature<Geometry, never>[] | Feature[]): FeatureCollection {
  return { type: "FeatureCollection", features: features as Feature[] };
}

/** Smooth, slightly curved route between two points (great for aid corridors). */
export function curvedPath(a: LngLat, b: LngLat, bend = 0.18, steps = 48): LngLat[] {
  const mid: LngLat = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const ctrl: LngLat = [mid[0] - dy * bend, mid[1] + dx * bend];
  const out: LngLat[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;
    out.push([
      u * u * a[0] + 2 * u * t * ctrl[0] + t * t * b[0],
      u * u * a[1] + 2 * u * t * ctrl[1] + t * t * b[1],
    ]);
  }
  return out;
}
