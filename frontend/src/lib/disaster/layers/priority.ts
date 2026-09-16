import { circleRing, fc, point, polygon } from "../geo";
import type { MapLayerModule, Scenario } from "../types";

/** AI priority regions — where the model recommends concentrating response. */
export const priorityLayer: MapLayerModule = {
  id: "priority",
  label: "AI Priority Regions",
  color: "#a78bfa",
  defaultVisible: true,
  build(scenario: Scenario) {
    const polys = scenario.priority.map((z, i) =>
      polygon(circleRing(z.center, z.radiusKm * 2.1, 64), { rank: i + 1, name: z.name }),
    );
    const labels = scenario.priority.map((z, i) => point(z.center, { label: `PRIORITY ${i + 1} · ${z.name}` }));

    return {
      sources: { "priority-areas": fc(polys), "priority-labels": fc(labels) },
      layers: [
        {
          id: "priority-outline",
          type: "line",
          source: "priority-areas",
          paint: {
            "line-color": "#c4b5fd",
            "line-width": 2,
            "line-dasharray": [1, 2],
            "line-opacity": 0.9,
          },
        },
        {
          id: "priority-label",
          type: "symbol",
          source: "priority-labels",
          layout: {
            "text-field": ["get", "label"],
            "text-size": 10,
            "text-letter-spacing": 0.12,
            "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
            "text-offset": [0, 3.4],
            "text-optional": true,
          },
          paint: { "text-color": "#ddd6fe", "text-halo-color": "#1e1b4b", "text-halo-width": 1.6 },
        },
      ],
    };
  },
};
