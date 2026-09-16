import { useEffect, useRef } from "react";
import type * as GeoJSON from "geojson";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import {
  DISASTER_COLOR,
  SEVERITY_RADIUS,
  blobPolygon,
  circlePolygon,
  deploymentsFor,
  facilitiesFor,
  incidentsFor,
  offset,
  zoneOf,
  type Incident,
  type Scenario,
} from "@/lib/scenario";
import { createThreeEffectLayer } from "./three-effect";

export type MapMode = "satellite" | "3d";

export interface LayerToggles {
  zones: boolean;
  routes: boolean;
  resources: boolean;
  facilities: boolean;
  incidents: boolean;
  priority: boolean;
}

interface Props {
  scenario: Scenario;
  mode: MapMode;
  layers: LayerToggles;
  onSelectIncident: (incident: Incident) => void;
}

const STYLES: Record<MapMode, string> = {
  satellite: "mapbox://styles/mapbox/satellite-streets-v12",
  "3d": "mapbox://styles/mapbox/dark-v11",
};

type FC = GeoJSON.FeatureCollection<GeoJSON.Geometry, Record<string, unknown>>;

function fc(features: GeoJSON.Feature<GeoJSON.Geometry, Record<string, unknown>>[]): FC {
  return { type: "FeatureCollection", features };
}

function poly(coords: [number, number][], props: Record<string, unknown> = {}) {
  return {
    type: "Feature" as const,
    properties: props,
    geometry: { type: "Polygon" as const, coordinates: [coords] },
  };
}

function line(coords: [number, number][], props: Record<string, unknown> = {}) {
  return {
    type: "Feature" as const,
    properties: props,
    geometry: { type: "LineString" as const, coordinates: coords },
  };
}

export default function DisasterMap({ scenario, mode, layers, onSelectIncident }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const scenarioRef = useRef(scenario);
  const layersRef = useRef(layers);
  const modeRef = useRef(mode);
  const selectRef = useRef(onSelectIncident);
  scenarioRef.current = scenario;
  layersRef.current = layers;
  selectRef.current = onSelectIncident;

  const token = import.meta.env["VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN"] as string | undefined;

  /* ---------- build every overlay for the current scenario ---------- */
  function paint(map: mapboxgl.Map) {
    const s = scenarioRef.current;
    const zone = zoneOf(s);
    const center = zone.center;
    const r = SEVERITY_RADIUS[s.severity];
    const color = DISASTER_COLOR[s.disasterType];
    const is3d = modeRef.current === "3d";

    // ---- terrain / buildings / sky for 3D mode
    if (is3d) {
      if (!map.getSource("mapbox-dem")) {
        map.addSource("mapbox-dem", {
          type: "raster-dem",
          url: "mapbox://mapbox.mapbox-terrain-dem-v1",
          tileSize: 512,
          maxzoom: 14,
        });
      }
      map.setTerrain({ source: "mapbox-dem", exaggeration: 1.3 });
      if (!map.getLayer("sky")) {
        map.addLayer({
          id: "sky",
          type: "sky",
          paint: {
            "sky-type": "atmosphere",
            "sky-atmosphere-sun-intensity": 6,
          },
        });
      }
      if (!map.getLayer("buildings-3d")) {
        map.addLayer({
          id: "buildings-3d",
          source: "composite",
          "source-layer": "building",
          type: "fill-extrusion",
          minzoom: 12,
          filter: ["==", ["get", "extrude"], "true"],
          paint: {
            "fill-extrusion-color": "#1e293b",
            "fill-extrusion-height": ["get", "height"],
            "fill-extrusion-base": ["get", "min_height"],
            "fill-extrusion-opacity": 0.85,
          },
        });
      }
    }

    /* ---- disaster footprint sources ---- */
    const impact: GeoJSON.Feature<GeoJSON.Geometry, Record<string, unknown>>[] = [];
    const rings: GeoJSON.Feature<GeoJSON.Geometry, Record<string, unknown>>[] = [];
    const heat: GeoJSON.Feature<GeoJSON.Geometry, Record<string, unknown>>[] = [];
    const tracks: GeoJSON.Feature<GeoJSON.Geometry, Record<string, unknown>>[] = [];

    switch (s.disasterType) {
      case "flood":
        impact.push(poly(blobPolygon(center, r, 1), { shade: 0.55 }));
        impact.push(poly(blobPolygon(center, r * 0.6, 3), { shade: 0.8 }));
        impact.push(poly(blobPolygon(offset(center, r * 0.8, 120), r * 0.5, 5), { shade: 0.5 }));
        break;
      case "fire":
        impact.push(poly(blobPolygon(center, r * 0.75, 2), { shade: 0.75 }));
        heat.push(poly(blobPolygon(center, r * 1.25, 4), { shade: 0.35 }));
        break;
      case "earthquake":
        [0.4, 0.7, 1, 1.35].forEach((f, i) =>
          rings.push(poly(circlePolygon(center, r * f), { level: i })),
        );
        impact.push(poly(circlePolygon(center, r * 0.28), { shade: 0.85 }));
        break;
      case "heavy_rain":
        [1.4, 1, 0.6, 0.3].forEach((f, i) =>
          heat.push(poly(blobPolygon(center, r * f, i + 1), { shade: 0.2 + i * 0.18 })),
        );
        break;
      case "cyclone": {
        const track: [number, number][] = [-3, -1.6, 0, 1.8, 3.6].map((k) =>
          offset(center, r * 4 * k, 215),
        );
        tracks.push(line(track, { kind: "track" }));
        const coneCoords: [number, number][] = [
          ...track.map((p, i) => offset(p, r * (0.4 + i * 0.7), 125)),
          ...[...track].reverse().map((p, i) => offset(p, r * (0.4 + (4 - i) * 0.7), 305)),
        ];
        impact.push(poly(coneCoords, { shade: 0.3 }));
        impact.push(poly(circlePolygon(center, r * 0.8), { shade: 0.7 }));
        break;
      }
      case "landslide": {
        const debris: [number, number][] = [
          offset(center, r * 0.2, 0),
          offset(center, r * 0.9, 150),
          offset(center, r * 1.4, 175),
          offset(center, r * 1.1, 205),
          offset(center, r * 0.4, 320),
        ];
        impact.push(poly(debris, { shade: 0.7 }));
        heat.push(poly(circlePolygon(center, r * 1.5), { shade: 0.25 }));
        break;
      }
    }

    const affected = [poly(circlePolygon(center, r * 1.9), { shade: 0.12 })];
    const priority = [
      poly(circlePolygon(offset(center, r * 0.9, 55), r * 0.55), { rank: 1 }),
      poly(circlePolygon(offset(center, r * 1.2, 235), r * 0.45), { rank: 2 }),
    ];

    const deployments = deploymentsFor(s);
    const routes = deployments.map((d) =>
      line(d.path, { color: d.color, label: `${d.unit} · ETA ${d.etaMins}m`, status: d.status }),
    );
    const staging = deployments.map((d) => ({
      type: "Feature" as const,
      properties: { color: d.color },
      geometry: { type: "Point" as const, coordinates: d.path[0]! },
    }));

    const data: Record<string, FC> = {
      "dr-affected": fc(affected),
      "dr-impact": fc(impact),
      "dr-heat": fc(heat),
      "dr-rings": fc(rings),
      "dr-tracks": fc(tracks),
      "dr-priority": fc(priority),
      "dr-routes": fc(routes),
      "dr-staging": fc(staging),
    };

    Object.entries(data).forEach(([id, geojson]) => {
      const existing = map.getSource(id) as mapboxgl.GeoJSONSource | undefined;
      if (existing) existing.setData(geojson as GeoJSON.GeoJSON);
      else map.addSource(id, { type: "geojson", data: geojson as GeoJSON.GeoJSON });
    });

    const add = (layer: mapboxgl.AnyLayer) => {
      if (!map.getLayer((layer as { id: string }).id)) map.addLayer(layer as never);
    };

    add({
      id: "dr-affected-fill",
      type: "fill",
      source: "dr-affected",
      paint: { "fill-color": color, "fill-opacity": 0.1 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-affected-line",
      type: "line",
      source: "dr-affected",
      paint: {
        "line-color": color,
        "line-width": 1.5,
        "line-dasharray": [3, 2],
        "line-opacity": 0.7,
      },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-heat-fill",
      type: "fill",
      source: "dr-heat",
      paint: {
        "fill-color": s.disasterType === "heavy_rain" ? "#22d3ee" : color,
        "fill-opacity": ["*", ["get", "shade"], 0.9],
      },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-impact-fill",
      type: "fill",
      source: "dr-impact",
      paint: { "fill-color": color, "fill-opacity": ["get", "shade"] },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-impact-line",
      type: "line",
      source: "dr-impact",
      paint: { "line-color": color, "line-width": 2, "line-opacity": 0.9 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-rings-line",
      type: "line",
      source: "dr-rings",
      paint: { "line-color": color, "line-width": 2, "line-opacity": 0.85 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-tracks-line",
      type: "line",
      source: "dr-tracks",
      paint: {
        "line-color": color,
        "line-width": 3,
        "line-dasharray": [2, 1.5],
      },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-priority-fill",
      type: "fill",
      source: "dr-priority",
      paint: { "fill-color": "#f59e0b", "fill-opacity": 0.16 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-priority-line",
      type: "line",
      source: "dr-priority",
      paint: { "line-color": "#fbbf24", "line-width": 2, "line-dasharray": [1, 1] },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-routes-casing",
      type: "line",
      source: "dr-routes",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#0b1220", "line-width": 7, "line-opacity": 0.7 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-routes-line",
      type: "line",
      source: "dr-routes",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ["get", "color"],
        "line-width": 3.2,
        "line-dasharray": [1.6, 1.2],
      },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-routes-label",
      type: "symbol",
      source: "dr-routes",
      layout: {
        "symbol-placement": "line-center",
        "text-field": ["get", "label"],
        "text-size": 11,
      },
      paint: { "text-color": "#e2e8f0", "text-halo-color": "#0b1220", "text-halo-width": 1.6 },
    } as mapboxgl.AnyLayer);
    add({
      id: "dr-staging-point",
      type: "circle",
      source: "dr-staging",
      paint: {
        "circle-radius": 6,
        "circle-color": ["get", "color"],
        "circle-stroke-color": "#0b1220",
        "circle-stroke-width": 2,
      },
    } as mapboxgl.AnyLayer);

    if (is3d && !map.getLayer("three-effect")) {
      map.addLayer(createThreeEffectLayer(center, color, r));
    }

    applyVisibility(map);
    placeMarkers(map);
  }

  function applyVisibility(map: mapboxgl.Map) {
    const l = layersRef.current;
    const groups: Record<string, string[]> = {
      zones: [
        "dr-affected-fill",
        "dr-affected-line",
        "dr-impact-fill",
        "dr-impact-line",
        "dr-heat-fill",
        "dr-rings-line",
        "dr-tracks-line",
        "three-effect",
      ],
      routes: ["dr-routes-casing", "dr-routes-line", "dr-routes-label"],
      resources: ["dr-staging-point"],
      priority: ["dr-priority-fill", "dr-priority-line"],
    };
    Object.entries(groups).forEach(([key, ids]) => {
      const visible = l[key as keyof LayerToggles];
      ids.forEach((id) => {
        if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
      });
    });
  }

  function placeMarkers(map: mapboxgl.Map) {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
    const s = scenarioRef.current;
    const l = layersRef.current;

    if (l.facilities) {
      facilitiesFor(s).forEach((f) => {
        const el = document.createElement("div");
        el.className = `map-pin map-pin-${f.kind}`;
        el.style.cssText = "width:24px;height:24px;border-radius:50%;background:#38bdf8;color:#0b1220;display:grid;place-items:center;font-weight:bold;font-size:11px;border:2px solid #0b1220;cursor:pointer;";
        el.innerHTML = `<span>${f.kind === "hospital" ? "H" : f.kind === "shelter" ? "S" : "W"}</span>`;
        const marker = new mapboxgl.Marker({ element: el })
          .setLngLat(f.coord)
          .setPopup(
            new mapboxgl.Popup({ offset: 16, closeButton: false }).setHTML(
              `<strong>${f.name}</strong><br/>${f.kind} · capacity ${f.capacity}<br/>occupied ${f.occupied}`,
            ),
          )
          .addTo(map);
        markersRef.current.push(marker);
      });
    }

    if (l.incidents) {
      incidentsFor(s).forEach((inc, i) => {
        const el = document.createElement("div");
        el.className = `map-pin map-pin-incident${i === 0 ? " map-pin-primary" : ""}`;
        el.style.cssText = `width:26px;height:26px;border-radius:50%;background:${i === 0 ? "#f43f5e" : "#fb923c"};color:#fff;display:grid;place-items:center;font-weight:bold;font-size:13px;border:2px solid #fff;cursor:pointer;box-shadow:0 0 10px ${i === 0 ? "rgba(244,63,94,0.8)" : "rgba(251,146,60,0.6)"};`;
        el.innerHTML = "<span>!</span>";
        el.addEventListener("click", () => selectRef.current(inc));
        const marker = new mapboxgl.Marker({ element: el }).setLngLat(inc.coord).addTo(map);
        markersRef.current.push(marker);
      });
    }
  }

  /* ---------- init ---------- */
  useEffect(() => {
    if (!containerRef.current || mapRef.current || !token) return;
    mapboxgl.accessToken = token;
    const zone = zoneOf(scenarioRef.current);
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: STYLES[modeRef.current],
      center: zone.center,
      zoom: 13,
      pitch: modeRef.current === "3d" ? 62 : 0,
      bearing: modeRef.current === "3d" ? -22 : 0,
      antialias: true,
      attributionControl: false,
    });
    mapRef.current = map;
    map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");
    map.on("style.load", () => paint(map));
    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  /* ---------- mode switch ---------- */
  useEffect(() => {
    const map = mapRef.current;
    modeRef.current = mode;
    if (!map) return;
    map.setStyle(STYLES[mode]);
    map.easeTo({
      pitch: mode === "3d" ? 62 : 0,
      bearing: mode === "3d" ? -22 : 0,
      zoom: mode === "3d" ? 14 : 13,
      duration: 900,
    });
  }, [mode]);

  /* ---------- scenario / layer updates ---------- */
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    paint(map);
    map.easeTo({ center: zoneOf(scenario).center, duration: 800 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    applyVisibility(map);
    placeMarkers(map);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layers]);

  if (!token) {
    return (
      <div className="flex h-full items-center justify-center bg-card p-8 text-center text-sm text-muted-foreground">
        Map credentials are unavailable. Reconnect Mapbox to load the live map.
      </div>
    );
  }

  return <div ref={containerRef} className="h-full w-full" />;
}
