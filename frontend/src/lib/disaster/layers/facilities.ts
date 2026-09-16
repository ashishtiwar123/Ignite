import { fc, point } from "../geo";
import type { MapLayerModule, Scenario } from "../types";

/** Shelters, hospitals and supply warehouses. */
export const facilitiesLayer: MapLayerModule = {
  id: "facilities",
  label: "Shelters & Facilities",
  color: "#22c55e",
  defaultVisible: true,
  build(scenario: Scenario) {
    const pts = scenario.facilities.map((f) =>
      point(f.center, {
        id: f.id,
        name: f.name,
        kind: f.kind,
        glyph: f.kind === "shelter" ? "SH" : f.kind === "hospital" ? "H" : "WH",
        sub: `${f.occupied}/${f.capacity}`,
      }),
    );

    return {
      sources: { "facilities-points": fc(pts) },
      layers: [
        {
          id: "facilities-halo",
          type: "circle",
          source: "facilities-points",
          paint: {
            "circle-radius": 16,
            "circle-color": ["match", ["get", "kind"], "hospital", "#ef4444", "warehouse", "#f59e0b", "#22c55e"],
            "circle-opacity": 0.18,
          },
        },
        {
          id: "facilities-dot",
          type: "circle",
          source: "facilities-points",
          paint: {
            "circle-radius": 10,
            "circle-color": ["match", ["get", "kind"], "hospital", "#ef4444", "warehouse", "#f59e0b", "#22c55e"],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        },
        {
          id: "facilities-glyph",
          type: "symbol",
          source: "facilities-points",
          layout: {
            "text-field": ["get", "glyph"],
            "text-size": 9,
            "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
          },
          paint: { "text-color": "#04140a" },
        },
        {
          id: "facilities-label",
          type: "symbol",
          source: "facilities-points",
          layout: {
            "text-field": ["concat", ["get", "name"], "  ", ["get", "sub"]],
            "text-size": 11,
            "text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
            "text-offset": [0, 1.5],
            "text-optional": true,
          },
          paint: { "text-color": "#eafff2", "text-halo-color": "#04140a", "text-halo-width": 1.6 },
        },
      ],
    };
  },
};
