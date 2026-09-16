import { fc, line, point } from "../geo";
import type { MapLayerModule, Scenario } from "../types";

/** Aid corridors — the route each resource is taking to reach a zone. */
export const routesLayer: MapLayerModule = {
  id: "routes",
  label: "Aid Routes",
  color: "#34d399",
  defaultVisible: true,
  build(scenario: Scenario) {
    const lines = scenario.deployments.map((d) =>
      line(d.path, { unit: d.unit, status: d.status, eta: d.etaMin, resource: d.resource }),
    );
    const labels = scenario.deployments.map((d) => {
      const mid = d.path[Math.floor(d.path.length / 2)]!;
      return point(mid, { label: `${d.unit} · ${d.resource} · ETA ${d.etaMin}m` });
    });
    const heads = scenario.deployments.map((d) => point(d.path[d.path.length - 1]!, { status: d.status }));

    return {
      sources: { "routes-lines": fc(lines), "routes-labels": fc(labels), "routes-heads": fc(heads) },
      layers: [
        {
          id: "routes-casing",
          type: "line",
          source: "routes-lines",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#022c22", "line-width": 7, "line-opacity": 0.55, "line-blur": 1 },
        },
        {
          id: "routes-line",
          type: "line",
          source: "routes-lines",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": [
              "match",
              ["get", "status"],
              "on-site",
              "#22c55e",
              "staging",
              "#facc15",
              "#38bdf8",
            ],
            "line-width": 3,
            "line-dasharray": [1.5, 1.2],
          },
        },
        {
          id: "routes-head",
          type: "circle",
          source: "routes-heads",
          paint: {
            "circle-radius": 6,
            "circle-color": ["match", ["get", "status"], "on-site", "#22c55e", "staging", "#facc15", "#38bdf8"],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
          },
        },
        {
          id: "routes-label",
          type: "symbol",
          source: "routes-labels",
          layout: {
            "text-field": ["get", "label"],
            "text-size": 11,
            "text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
            "text-offset": [0, 1.2],
          },
          paint: { "text-color": "#d1fae5", "text-halo-color": "#022c22", "text-halo-width": 1.6 },
        },
      ],
    };
  },
};
