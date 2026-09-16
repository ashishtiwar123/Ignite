import { blobRing, circleRing, destination, fc, line, point, polygon, mulberry32, hashString } from "../geo";
import type { MapLayerModule, Scenario } from "../types";
import type { Feature } from "geojson";

/**
 * Hazard layer — the physical disaster footprint itself.
 * Each disaster type renders its own realistic representation.
 */
export const hazardLayer: MapLayerModule = {
  id: "hazard",
  label: "Disaster Overlay",
  color: "#38bdf8",
  defaultVisible: true,
  build(scenario: Scenario) {
    const type = scenario.input.disasterType;
    const rnd = mulberry32(hashString(scenario.title));
    const areas: Feature[] = [];
    const accents: Feature[] = [];
    const rings: Feature[] = [];
    const heat: Feature[] = [];

    if (type === "flood") {
      scenario.zones.forEach((z, i) => {
        areas.push(polygon(blobRing(z.center, z.radiusKm * 1.35, i + 7), { depth: z.waterLevel ?? 1 }));
        areas.push(polygon(blobRing(z.center, z.radiusKm * 0.7, i + 21), { depth: (z.waterLevel ?? 1) + 1 }));
        // flow / debris direction streaks
        for (let k = 0; k < 6; k++) {
          const b = rnd() * 360;
          const a = destination(z.center, z.radiusKm * 0.3 + rnd() * z.radiusKm, b);
          accents.push(line([a, destination(a, 0.35, b + 90)], {}));
        }
      });
    }

    if (type === "fire") {
      scenario.zones.forEach((z, i) => {
        areas.push(polygon(blobRing(z.center, z.radiusKm * 1.3, i + 3, 0.5), { depth: 1 }));
        areas.push(polygon(blobRing(z.center, z.radiusKm * 0.65, i + 31, 0.5), { depth: 3 }));
        for (let k = 0; k < 14; k++) {
          heat.push(point(destination(z.center, rnd() * z.radiusKm, rnd() * 360), { intensity: rnd() }));
        }
      });
    }

    if (type === "earthquake") {
      const epi = scenario.zones[0]?.center ?? scenario.center;
      [1, 2, 3.2, 4.8, 6.5].forEach((r, i) => {
        rings.push(polygon(circleRing(epi, r), { level: i }));
      });
      accents.push(point(epi, { epicenter: 1 }));
    }

    if (type === "rain") {
      const cells = 260;
      for (let i = 0; i < cells; i++) {
        const p = destination(scenario.center, rnd() * 9, rnd() * 360);
        heat.push(point(p, { intensity: Math.pow(rnd(), 1.6) }));
      }
      scenario.zones.forEach((z) => {
        for (let i = 0; i < 40; i++) {
          heat.push(point(destination(z.center, rnd() * z.radiusKm * 1.6, rnd() * 360), { intensity: 0.7 + rnd() * 0.3 }));
        }
      });
    }

    if (type === "cyclone") {
      const start = destination(scenario.center, 45, 200);
      const track: [number, number][] = [];
      for (let i = 0; i <= 8; i++) {
        track.push(destination(start, (i / 8) * 55, 20 + i * 2));
      }
      accents.push(line(track, { kind: "track" }));
      // forecast cone
      const left = track.map((p, i) => destination(p, 1 + (i / 8) * 14, 290));
      const right = [...track].reverse().map((p, i) => destination(p, 1 + ((8 - i) / 8) * 14, 110));
      areas.push(polygon([...left, ...right, left[0]!], { depth: 1 }));
      const eye = track[track.length - 1]!;
      [3, 8, 16, 26].forEach((r, i) => rings.push(polygon(circleRing(eye, r), { level: i })));
      accents.push(point(eye, { epicenter: 1 }));
    }

    const palette: Record<string, { fill: string; strong: string; accent: string }> = {
      flood: { fill: "#1d7fe0", strong: "#0b4f9e", accent: "#7dd3fc" },
      fire: { fill: "#f97316", strong: "#dc2626", accent: "#fde047" },
      earthquake: { fill: "#f43f5e", strong: "#b91c1c", accent: "#fda4af" },
      rain: { fill: "#22d3ee", strong: "#2563eb", accent: "#a5f3fc" },
      cyclone: { fill: "#60a5fa", strong: "#1e40af", accent: "#e0f2fe" },
    };
    const c = palette[type]!;

    return {
      sources: {
        "hazard-areas": fc(areas),
        "hazard-accents": fc(accents),
        "hazard-rings": fc(rings),
        "hazard-heat": fc(heat),
      },
      layers: [
        {
          id: "hazard-area-fill",
          type: "fill",
          source: "hazard-areas",
          paint: {
            "fill-color": ["interpolate", ["linear"], ["get", "depth"], 0, c.fill, 4, c.strong],
            "fill-opacity": type === "cyclone" ? 0.22 : 0.42,
          },
        },
        {
          id: "hazard-area-line",
          type: "line",
          source: "hazard-areas",
          paint: { "line-color": c.accent, "line-width": 1.4, "line-opacity": 0.75 },
        },
        {
          id: "hazard-heat",
          type: "heatmap",
          source: "hazard-heat",
          paint: {
            "heatmap-weight": ["get", "intensity"],
            "heatmap-intensity": 1.1,
            "heatmap-radius": type === "rain" ? 42 : 30,
            "heatmap-opacity": 0.75,
            "heatmap-color": [
              "interpolate",
              ["linear"],
              ["heatmap-density"],
              0,
              "rgba(0,0,0,0)",
              0.2,
              type === "rain" ? "#1d4ed8" : "#7c2d12",
              0.45,
              type === "rain" ? "#22c55e" : "#ea580c",
              0.7,
              type === "rain" ? "#facc15" : "#f97316",
              1,
              type === "rain" ? "#ef4444" : "#fde047",
            ],
          },
        },
        {
          id: "hazard-rings",
          type: "line",
          source: "hazard-rings",
          paint: {
            "line-color": c.accent,
            "line-width": ["interpolate", ["linear"], ["get", "level"], 0, 3, 4, 1],
            "line-opacity": ["interpolate", ["linear"], ["get", "level"], 0, 0.95, 4, 0.35],
          },
        },
        {
          id: "hazard-accent-line",
          type: "line",
          source: "hazard-accents",
          filter: ["==", ["geometry-type"], "LineString"],
          paint: {
            "line-color": c.accent,
            "line-width": type === "cyclone" ? 2.5 : 1.2,
            "line-opacity": 0.9,
            "line-dasharray": [2, 1.5],
          },
        },
        {
          id: "hazard-epicenter",
          type: "circle",
          source: "hazard-accents",
          filter: ["==", ["geometry-type"], "Point"],
          paint: {
            "circle-radius": 7,
            "circle-color": c.strong,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        },
      ],
    };
  },
};
