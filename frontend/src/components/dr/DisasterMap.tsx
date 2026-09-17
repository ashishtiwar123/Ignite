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
  heavyRainDetailsFor,
  incidentsFor,
  offset,
  zoneOf,
  type Incident,
  type Scenario,
} from "@/lib/scenario";

export type MapMode = "satellite" | "3d";

export interface LayerToggles {
  zones: boolean;
  routes: boolean;
  resources: boolean;
  facilities: boolean;
  incidents: boolean;
}

import type { IncidentSummaryResponse } from "@/lib/api/types";

interface Props {
  scenario: Scenario;
  mode: MapMode;
  layers: LayerToggles;
  onSelectIncident: (incident: Incident) => void;
  backendIncidents?: IncidentSummaryResponse[];
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

function isValidCoordinate(lat: unknown, lng: unknown): lat is number {
  return (
    typeof lat === "number" &&
    typeof lng === "number" &&
    !Number.isNaN(lat) &&
    !Number.isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
}

export default function DisasterMap({
  scenario,
  mode,
  layers,
  onSelectIncident,
  backendIncidents,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const currentStyleRef = useRef<string | null>(null);
  const scenarioRef = useRef(scenario);
  const layersRef = useRef(layers);
  const modeRef = useRef(mode);
  const selectRef = useRef(onSelectIncident);
  const backendIncidentsRef = useRef(backendIncidents);
  scenarioRef.current = scenario;
  layersRef.current = layers;
  selectRef.current = onSelectIncident;
  backendIncidentsRef.current = backendIncidents;

  const token = (import.meta.env["VITE_MAPBOX_PUBLIC_TOKEN"] ??
    import.meta.env["VITE_MAPBOX_TOKEN"] ??
    import.meta.env["VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN"]) as string | undefined;

  /* ---------- build every overlay for the current scenario ---------- */
  function paint(map: mapboxgl.Map) {
    if (!map || !map.getStyle()) return;

    const s = scenarioRef.current;
    const zone = zoneOf(s);
    const center = zone.center;
    const r = SEVERITY_RADIUS[s.severity];
    const color = DISASTER_COLOR[s.disasterType];
    const is3d = modeRef.current === "3d";

    // ---- 3D building extrusions for 3D mode
    if (is3d && map.getSource("composite")) {
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
        // Realistic multi-tier water inundation zone
        impact.push(poly(blobPolygon(center, r * 1.1, 1), { shade: 0.45, label: "Outer Flood Inundation Zone" }));
        impact.push(poly(blobPolygon(center, r * 0.7, 3), { shade: 0.7, label: "Deep Water Core Submergence" }));
        impact.push(poly(blobPolygon(offset(center, r * 0.6, 135), r * 0.45, 5), { shade: 0.55, label: "River Overflow Pocket" }));
        rings.push(poly(circlePolygon(center, r * 1.3), { level: 1 }));
        rings.push(poly(circlePolygon(center, r * 0.85), { level: 2 }));
        break;
      case "fire": {
        // Tightly concentrated, intense wildfire outbreak zone
        const rf = r * 0.28; // Scale down fire footprint so it stays localized (~200m-600m)
        impact.push(poly(blobPolygon(center, rf * 0.4, 2), { shade: 0.85, label: "Active Blaze Core" }));
        impact.push(poly(blobPolygon(center, rf * 0.75, 4), { shade: 0.6, label: "Active Flame Front" }));
        heat.push(poly(blobPolygon(offset(center, rf * 0.15, 45), rf * 1.05, 7), { shade: 0.35, label: "Thermal Heat Envelope" }));
        rings.push(poly(circlePolygon(center, rf * 1.3), { level: 1, label: "Containment Firebreak" }));
        break;
      }
      case "earthquake":
        [0.4, 0.7, 1, 1.35].forEach((f, i) =>
          rings.push(poly(circlePolygon(center, r * f), { level: i })),
        );
        impact.push(poly(circlePolygon(center, r * 0.28), { shade: 0.85 }));
        break;
      case "heavy_rain": {
        // Multi-tier Doppler precipitation radar reflectivity bands (distinct cyan/teal downpour cells)
        heat.push(poly(blobPolygon(center, r * 0.35, 1), { shade: 0.8, label: "Torrential Cloudburst Cell Core" }));
        heat.push(poly(blobPolygon(center, r * 0.75, 3), { shade: 0.55, label: "Heavy Downpour Precipitation Band" }));
        heat.push(poly(blobPolygon(offset(center, r * 0.25, 130), r * 1.25, 5), { shade: 0.32, label: "Rain Storm System Envelope" }));

        // Isohyet Rainfall Accumulation Contour Rings (50mm, 100mm, 150mm Isohyets)
        rings.push(poly(circlePolygon(center, r * 0.5), { level: 1, label: "150mm Precipitation Contour" }));
        rings.push(poly(circlePolygon(center, r * 0.9), { level: 2, label: "100mm Precipitation Contour" }));
        rings.push(poly(circlePolygon(center, r * 1.4), { level: 3, label: "50mm Precipitation Contour" }));
        break;
      }
      case "cyclone": {
        // High-precision cyclone trajectory & probability uncertainty cone matching real forecast tracks
        const trackCoords: [number, number][] = [
          offset(center, r * 3.8, 220), // Offshore origin
          offset(center, r * 2.0, 215), // Ocean storm position
          center,                       // Active storm eye position (target zone)
          offset(center, r * 1.8, 38),  // Coastal Landfall impact point
          offset(center, r * 3.4, 32),  // Inland dissipation path
        ];
        tracks.push(line(trackCoords, { kind: "forecast_track" }));

        // Cone of Uncertainty (Probability Cone spreading along forecast path)
        const coneLeft = trackCoords.map((p, i) => offset(p, r * (0.35 + i * 0.48), 128));
        const coneRight = [...trackCoords].reverse().map((p, i) =>
          offset(p, r * (0.35 + (4 - i) * 0.48), 308),
        );
        const conePolygonCoords = [...coneLeft, ...coneRight, coneLeft[0]!];
        impact.push(poly(conePolygonCoords, { shade: 0.38, label: "Uncertainty Forecast Cone" }));

        // Eyewall Core & Swirling Wind Field Radii
        impact.push(poly(circlePolygon(center, r * 0.45), { shade: 0.75, label: "Eye Wall Destruction Core" }));
        rings.push(poly(circlePolygon(center, r * 1.2), { level: 1, label: "Hurricane Force Wind Radius" }));
        rings.push(poly(circlePolygon(center, r * 2.2), { level: 2, label: "Tropical Storm Wind Radius" }));
        break;
      }
    }

    const affectedRadiusMult = s.disasterType === "fire" ? 0.45 : 1.8;
    const affected = [poly(circlePolygon(center, r * affectedRadiusMult), { shade: 0.12 })];

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

    const setPaint = (layerId: string, name: string, value: unknown) => {
      if (map.getLayer(layerId)) map.setPaintProperty(layerId, name as never, value as never);
    };

    add({
      id: "dr-affected-fill",
      type: "fill",
      source: "dr-affected",
      paint: { "fill-color": color, "fill-opacity": 0.1 },
    } as mapboxgl.AnyLayer);
    setPaint("dr-affected-fill", "fill-color", color);

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
    setPaint("dr-affected-line", "line-color", color);

    add({
      id: "dr-heat-fill",
      type: "fill",
      source: "dr-heat",
      paint: {
        "fill-color": s.disasterType === "fire" ? "#f97316" : s.disasterType === "heavy_rain" ? "#10b981" : color,
        "fill-opacity": ["*", ["get", "shade"], 0.9],
      },
    } as mapboxgl.AnyLayer);
    setPaint("dr-heat-fill", "fill-color", s.disasterType === "fire" ? "#f97316" : s.disasterType === "heavy_rain" ? "#10b981" : color);

    add({
      id: "dr-impact-fill",
      type: "fill",
      source: "dr-impact",
      paint: { "fill-color": color, "fill-opacity": ["get", "shade"] },
    } as mapboxgl.AnyLayer);
    setPaint("dr-impact-fill", "fill-color", color);

    add({
      id: "dr-impact-line",
      type: "line",
      source: "dr-impact",
      paint: { "line-color": s.disasterType === "fire" ? "#dc2626" : s.disasterType === "heavy_rain" ? "#059669" : color, "line-width": 2, "line-opacity": 0.9 },
    } as mapboxgl.AnyLayer);
    setPaint("dr-impact-line", "line-color", s.disasterType === "fire" ? "#dc2626" : s.disasterType === "heavy_rain" ? "#059669" : color);

    add({
      id: "dr-rings-line",
      type: "line",
      source: "dr-rings",
      paint: { "line-color": s.disasterType === "fire" ? "#f43f5e" : s.disasterType === "heavy_rain" ? "#10b981" : color, "line-width": 2, "line-opacity": 0.85 },
    } as mapboxgl.AnyLayer);
    setPaint("dr-rings-line", "line-color", s.disasterType === "fire" ? "#f43f5e" : s.disasterType === "heavy_rain" ? "#10b981" : color);
    add({
      id: "dr-tracks-line",
      type: "line",
      source: "dr-tracks",
      paint: {
        "line-color": s.disasterType === "cyclone" ? "#e879f9" : color,
        "line-width": 3.5,
        "line-dasharray": [2, 1.5],
      },
    } as mapboxgl.AnyLayer);
    setPaint("dr-tracks-line", "line-color", s.disasterType === "cyclone" ? "#e879f9" : color);

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

    applyVisibility(map);
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
      ],
      routes: ["dr-routes-casing", "dr-routes-line", "dr-routes-label"],
      resources: ["dr-staging-point"],
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

    if (s.disasterType === "cyclone") {
      const zone = zoneOf(s);
      const center = zone.center;
      const r = SEVERITY_RADIUS[s.severity];
      const eyeCoord = center;
      const landfallCoord = offset(center, r * 1.8, 38);
      const originCoord = offset(center, r * 3.8, 220);

      // 1. Storm Eye Pin
      const eyeEl = document.createElement("div");
      eyeEl.style.cssText = "width:34px;height:34px;border-radius:50%;background:#a855f7;color:#fff;display:grid;place-items:center;font-weight:bold;font-size:16px;border:2px solid #fff;box-shadow:0 0 14px rgba(168,85,247,0.9);cursor:pointer;";
      eyeEl.innerHTML = "<span>🌀</span>";
      const eyeMarker = new mapboxgl.Marker({ element: eyeEl })
        .setLngLat(eyeCoord)
        .setPopup(new mapboxgl.Popup({ offset: 16, closeButton: false }).setHTML("<strong>Cyclone Eye Center</strong><br/>Active Storm Position"))
        .addTo(map);
      markersRef.current.push(eyeMarker);

      // 2. Projected Landfall Pin
      const lfEl = document.createElement("div");
      lfEl.style.cssText = "padding:4px 8px;border-radius:12px;background:#ef4444;color:#fff;font-weight:bold;font-size:10px;border:1.5px solid #fff;box-shadow:0 0 10px rgba(239,68,68,0.8);white-space:nowrap;";
      lfEl.innerHTML = "🎯 Landfall Target";
      const lfMarker = new mapboxgl.Marker({ element: lfEl })
        .setLngLat(landfallCoord)
        .setPopup(new mapboxgl.Popup({ offset: 16, closeButton: false }).setHTML("<strong>Projected Landfall Zone</strong><br/>High Impact Risk"))
        .addTo(map);
      markersRef.current.push(lfMarker);

      // 3. Origin Track Pin
      const origEl = document.createElement("div");
      origEl.style.cssText = "padding:3px 6px;border-radius:10px;background:#4b5563;color:#fff;font-weight:600;font-size:9px;border:1px solid #fff;opacity:0.85;";
      origEl.innerHTML = "Origin";
      const origMarker = new mapboxgl.Marker({ element: origEl }).setLngLat(originCoord).addTo(map);
      markersRef.current.push(origMarker);
    }

    if (l.facilities) {
      facilitiesFor(s).forEach((f) => {
        const el = document.createElement("div");
        el.className = `map-pin map-pin-${f.kind}`;
        el.style.cssText = "width:26px;height:26px;border-radius:50%;background:#0284c7;color:#ffffff;display:grid;place-items:center;font-weight:bold;font-size:12px;border:2px solid #ffffff;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.5);";
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
      if (backendIncidentsRef.current !== undefined) {
        backendIncidentsRef.current.forEach((inc, i) => {
          const lat = inc.centroid_latitude;
          const lng = inc.centroid_longitude;
          if (isValidCoordinate(lat, lng)) {
            const el = document.createElement("div");
            el.className = `map-pin map-pin-incident${i === 0 ? " map-pin-primary" : ""}`;
            el.style.cssText = `width:28px;height:28px;border-radius:50%;background:${i === 0 ? "#ef4444" : "#f97316"};color:#fff;display:grid;place-items:center;font-weight:bold;font-size:14px;border:2px solid #fff;cursor:pointer;box-shadow:0 0 12px ${i === 0 ? "rgba(239,68,68,0.9)" : "rgba(249,115,22,0.7)"};`;
            el.innerHTML = "<span>!</span>";
            el.addEventListener("click", () => {
              selectRef.current({
                id: inc.incident_id,
                title: `${inc.hazard_type} Incident`,
                detail: `Status: ${inc.status} · ID: ${inc.incident_id}`,
                coord: [lng, lat],
                severity: "high",
              });
            });
            const marker = new mapboxgl.Marker({ element: el })
              .setLngLat([lng, lat])
              .setPopup(
                new mapboxgl.Popup({ offset: 16 }).setHTML(
                  `<strong>${inc.hazard_type} Incident</strong><br/>ID: ${inc.incident_id.slice(0, 8)}...<br/>Status: ${inc.status}`
                )
              )
              .addTo(map);
            markersRef.current.push(marker);
          }
        });
      } else {
        incidentsFor(s).forEach((inc, i) => {
          const el = document.createElement("div");
          el.className = `map-pin map-pin-incident${i === 0 ? " map-pin-primary" : ""}`;
          el.style.cssText = `width:28px;height:28px;border-radius:50%;background:${i === 0 ? "#ef4444" : "#f97316"};color:#fff;display:grid;place-items:center;font-weight:bold;font-size:14px;border:2px solid #fff;cursor:pointer;box-shadow:0 0 12px ${i === 0 ? "rgba(239,68,68,0.9)" : "rgba(249,115,22,0.7)"};`;
          el.innerHTML = "<span>!</span>";
          el.addEventListener("click", () => selectRef.current(inc));
          const marker = new mapboxgl.Marker({ element: el }).setLngLat(inc.coord).addTo(map);
          markersRef.current.push(marker);
        });
      }
    }
  }

  /* ---------- init ---------- */
  useEffect(() => {
    if (!containerRef.current || mapRef.current || !token) return;
    mapboxgl.accessToken = token;
    const zone = zoneOf(scenarioRef.current);
    const initialStyle = STYLES[modeRef.current];
    currentStyleRef.current = initialStyle;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: initialStyle,
      center: zone.center,
      zoom: 13,
      pitch: modeRef.current === "3d" ? 62 : 0,
      bearing: modeRef.current === "3d" ? -22 : 0,
      antialias: true,
      attributionControl: false,
    });
    mapRef.current = map;
    map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");

    const renderAll = () => {
      if (!mapRef.current) return;
      paint(mapRef.current);
      placeMarkers(mapRef.current);
    };

    map.on("load", renderAll);
    map.on("style.load", renderAll);

    // Initial marker placement on DOM
    placeMarkers(map);

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      map.remove();
      mapRef.current = null;
      currentStyleRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  /* ---------- mode switch ---------- */
  useEffect(() => {
    const map = mapRef.current;
    modeRef.current = mode;
    if (!map) return;

    const targetStyle = STYLES[mode];
    if (currentStyleRef.current !== targetStyle) {
      currentStyleRef.current = targetStyle;

      map.once("style.load", () => {
        if (mapRef.current) {
          paint(mapRef.current);
          placeMarkers(mapRef.current);
        }
      });

      map.setStyle(targetStyle);
    } else {
      if (map.isStyleLoaded()) {
        paint(map);
      }
    }

    map.easeTo({
      pitch: mode === "3d" ? 62 : 0,
      bearing: mode === "3d" ? -22 : 0,
      zoom: mode === "3d" ? 14 : 13,
      duration: 900,
    });
    placeMarkers(map);
  }, [mode]);

  /* ---------- scenario / layer updates ---------- */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    placeMarkers(map);
    if (map.isStyleLoaded()) {
      paint(map);
      map.easeTo({ center: zoneOf(scenario).center, duration: 800 });
    } else {
      map.once("style.load", () => {
        if (mapRef.current) {
          paint(mapRef.current);
          mapRef.current.easeTo({ center: zoneOf(scenario).center, duration: 800 });
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    placeMarkers(map);
    if (map.isStyleLoaded()) {
      applyVisibility(map);
    } else {
      map.once("style.load", () => {
        if (mapRef.current) applyVisibility(mapRef.current);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layers]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    placeMarkers(map);
  }, [backendIncidents]);

  if (!token) {
    return (
      <div className="flex h-full items-center justify-center bg-card p-8 text-center text-sm text-muted-foreground">
        Map credentials are unavailable. Reconnect Mapbox to load the live map.
      </div>
    );
  }

  return (
    <div className="relative h-full w-full overflow-hidden">
      <div ref={containerRef} className="h-full w-full" />
      {scenario.disasterType === "heavy_rain" && <RainEffect severity={scenario.severity} />}
    </div>
  );
}

function RainEffect({ severity }: { severity: Scenario["severity"] }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    // Dynamic rain simulation intensity directly scaled by scenario severity
    const intensityMap: Record<
      Scenario["severity"],
      {
        count: number;
        speedMin: number;
        speedMax: number;
        lenMin: number;
        lenMax: number;
        widthMin: number;
        widthMax: number;
        opacityMin: number;
        opacityMax: number;
        slant: number;
        color: string;
      }
    > = {
      low: {
        count: 80,
        speedMin: 6,
        speedMax: 10,
        lenMin: 12,
        lenMax: 18,
        widthMin: 0.8,
        widthMax: 1.2,
        opacityMin: 0.25,
        opacityMax: 0.4,
        slant: 1.2,
        color: "rgba(110, 231, 183, ", // light emerald mist
      },
      moderate: {
        count: 180,
        speedMin: 12,
        speedMax: 18,
        lenMin: 18,
        lenMax: 28,
        widthMin: 1.0,
        widthMax: 1.6,
        opacityMin: 0.35,
        opacityMax: 0.6,
        slant: 2.5,
        color: "rgba(52, 211, 153, ", // steady teal rain
      },
      high: {
        count: 350,
        speedMin: 20,
        speedMax: 28,
        lenMin: 25,
        lenMax: 38,
        widthMin: 1.2,
        widthMax: 2.2,
        opacityMin: 0.45,
        opacityMax: 0.75,
        slant: 4.5,
        color: "rgba(16, 185, 129, ", // heavy rain
      },
      critical: {
        count: 600,
        speedMin: 28,
        speedMax: 42,
        lenMin: 35,
        lenMax: 55,
        widthMin: 1.5,
        widthMax: 2.8,
        opacityMin: 0.55,
        opacityMax: 0.9,
        slant: 7.0,
        color: "rgba(16, 185, 129, ", // torrential cloudburst downpour
      },
    };

    const cfg = intensityMap[severity] ?? intensityMap.high;

    const drops = Array.from({ length: cfg.count }, () => ({
      x: Math.random() * (width + 200),
      y: Math.random() * height,
      length: Math.random() * (cfg.lenMax - cfg.lenMin) + cfg.lenMin,
      speed: Math.random() * (cfg.speedMax - cfg.speedMin) + cfg.speedMin,
      opacity: Math.random() * (cfg.opacityMax - cfg.opacityMin) + cfg.opacityMin,
      width: Math.random() * (cfg.widthMax - cfg.widthMin) + cfg.widthMin,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.lineCap = "round";

      drops.forEach((d) => {
        ctx.beginPath();
        ctx.lineWidth = d.width;
        ctx.strokeStyle = `${cfg.color}${d.opacity})`;
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x - cfg.slant, d.y + d.length);
        ctx.stroke();

        d.x -= (cfg.slant / d.length) * (d.speed * 0.4);
        d.y += d.speed;

        if (d.y > height) {
          d.y = -d.length;
          d.x = Math.random() * (width + 200);
        }
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
    };
  }, [severity]);

  return <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 z-10 h-full w-full" />;
}

