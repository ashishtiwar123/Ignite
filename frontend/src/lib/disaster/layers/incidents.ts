import { fc, point } from "../geo";
import { SEVERITY_COLOR } from "../scenario";
import type { MapLayerModule, Scenario } from "../types";

/** Reported incident markers — clickable for details. */
export const incidentsLayer: MapLayerModule = {
  id: "incidents",
  label: "Incidents",
  color: "#f43f5e",
  defaultVisible: true,
  build(scenario: Scenario) {
    const pts = scenario.incidents.map((i) =>
      point(i.center, {
        id: i.id,
        title: i.title,
        zone: i.zone,
        detail: i.detail,
        severity: i.severity,
        color: SEVERITY_COLOR[i.severity],
      }),
    );

    return {
      sources: { "incidents-points": fc(pts) },
      layers: [
        {
          id: "incidents-pulse",
          type: "circle",
          source: "incidents-points",
          paint: { "circle-radius": 20, "circle-color": ["get", "color"], "circle-opacity": 0.16 },
        },
        {
          id: "incidents-dot",
          type: "circle",
          source: "incidents-points",
          paint: {
            "circle-radius": 9,
            "circle-color": ["get", "color"],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        },
        {
          id: "incidents-glyph",
          type: "symbol",
          source: "incidents-points",
          layout: {
            "text-field": "!",
            "text-size": 12,
            "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
          },
          paint: { "text-color": "#1a0208" },
        },
      ],
    };
  },
};
