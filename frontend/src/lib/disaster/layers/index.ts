import type { Map as MapboxMap, GeoJSONSource } from "mapbox-gl";
import type { MapLayerModule, Scenario } from "../types";

import { hazardLayer } from "./hazard";
import { zonesLayer } from "./zones";
import { routesLayer } from "./routes";
import { facilitiesLayer } from "./facilities";
import { incidentsLayer } from "./incidents";
import { priorityLayer } from "./priority";

/**
 * Layer registry. Order matters: earlier entries render underneath.
 * Add a new visualization by creating a module in this folder and appending it here.
 */
export const LAYER_MODULES: MapLayerModule[] = [
  hazardLayer,
  zonesLayer,
  priorityLayer,
  routesLayer,
  facilitiesLayer,
  incidentsLayer,
];

const layerIdsByModule = new Map<string, string[]>();

/** (Re)apply every registered layer to the map for the given scenario. */
export function applyLayers(map: MapboxMap, scenario: Scenario, visibility: Record<string, boolean>) {
  for (const mod of LAYER_MODULES) {
    const { sources, layers } = mod.build(scenario);

    for (const [id, data] of Object.entries(sources)) {
      const existing = map.getSource(id) as GeoJSONSource | undefined;
      if (existing) existing.setData(data);
      else map.addSource(id, { type: "geojson", data });
    }

    const ids: string[] = [];
    for (const spec of layers) {
      ids.push(spec.id);
      if (!map.getLayer(spec.id)) map.addLayer(spec);
      map.setLayoutProperty(spec.id, "visibility", visibility[mod.id] === false ? "none" : "visible");
    }
    layerIdsByModule.set(mod.id, ids);
  }
}

export function setLayerVisibility(map: MapboxMap, moduleId: string, visible: boolean) {
  for (const id of layerIdsByModule.get(moduleId) ?? []) {
    if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
  }
}

export const INTERACTIVE_LAYER_IDS = ["incidents-dot", "facilities-dot"];
