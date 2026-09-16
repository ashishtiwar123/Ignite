import { circleRing, fc, point, polygon } from "../geo";
import { SEVERITY_COLOR } from "../scenario";
import type { MapLayerModule, Scenario } from "../types";

/** Affected regions — administrative zone boundaries coloured by severity. */
export const zonesLayer: MapLayerModule = {
  id: "zones",
  label: "Affected Zones",
  color: "#fb923c",
  defaultVisible: true,
  build(scenario: Scenario) {
    const polys = scenario.zones.map((z) =>
      polygon(circleRing(z.center, z.radiusKm * 1.5, 64), {
        name: z.name,
        color: SEVERITY_COLOR[z.severity],
        affected: z.affected,
      }),
    );
    const labels = scenario.zones.map((z) =>
      point(z.center, { name: z.name, sub: `${z.affected.toLocaleString("en-IN")} affected` }),
    );

    return {
      sources: { "zones-areas": fc(polys), "zones-labels": fc(labels) },
      layers: [
        {
          id: "zones-outline",
          type: "line",
          source: "zones-areas",
          paint: { "line-color": ["get", "color"], "line-width": 2, "line-opacity": 0.85, "line-dasharray": [3, 2] },
        },
        {
          id: "zones-glow",
          type: "fill",
          source: "zones-areas",
          paint: { "fill-color": ["get", "color"], "fill-opacity": 0.08 },
        },
        {
          id: "zones-label",
          type: "symbol",
          source: "zones-labels",
          layout: {
            "text-field": ["concat", ["get", "name"], "\n", ["get", "sub"]],
            "text-size": 12,
            "text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
            "text-offset": [0, -1.6],
            "text-allow-overlap": false,
          },
          paint: { "text-color": "#ffffff", "text-halo-color": "#020617", "text-halo-width": 1.6 },
        },
      ],
    };
  },
};
