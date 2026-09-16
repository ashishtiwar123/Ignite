import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import { applyLayers, setLayerVisibility, INTERACTIVE_LAYER_IDS } from "@/lib/disaster/layers";
import type { Scenario } from "@/lib/disaster/types";

export interface MapSelection {
  title: string;
  subtitle: string;
  detail: string;
}

interface Props {
  scenario: Scenario;
  visibility: Record<string, boolean>;
  flyTo?: { center: [number, number]; zoom?: number; nonce: number } | null;
  onSelect: (sel: MapSelection) => void;
}

export default function MapCanvas({ scenario, visibility, flyTo, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const readyRef = useRef(false);

  useEffect(() => {
    const token = (import.meta.env["VITE_MAPBOX_PUBLIC_TOKEN"] ??
      import.meta.env["VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN"]) as string | undefined;
    if (!containerRef.current || !token) return;
    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      center: scenario.center,
      zoom: scenario.zoom,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
      projection: "mercator",
    });
    mapRef.current = map;

    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "bottom-right");
    map.addControl(new mapboxgl.ScaleControl({ unit: "metric" }), "bottom-left");
    map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-right");
    map.dragRotate.disable();
    map.touchZoomRotate.disableRotation();

    map.on("load", () => {
      readyRef.current = true;
      applyLayers(map, scenario, visibility);

      for (const id of INTERACTIVE_LAYER_IDS) {
        map.on("click", id, (e) => {
          const f = e.features?.[0];
          if (!f) return;
          const p = f.properties ?? {};
          onSelect({
            title: (p["title"] as string) ?? (p["name"] as string) ?? "Selected",
            subtitle: (p["zone"] as string) ?? (p["kind"] as string) ?? "",
            detail: (p["detail"] as string) ?? (p["sub"] ? `Occupancy ${p["sub"]}` : ""),
          });
        });
        map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
      }
    });

    return () => {
      readyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rebuild layers when the scenario changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    applyLayers(map, scenario, visibility);
    map.flyTo({ center: scenario.center, zoom: scenario.zoom, duration: 1200 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  // Toggle layer visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    for (const [id, visible] of Object.entries(visibility)) setLayerVisibility(map, id, visible);
  }, [visibility]);

  // External fly-to requests (clicking a zone / incident in a panel)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !flyTo) return;
    map.flyTo({ center: flyTo.center, zoom: flyTo.zoom ?? 13.4, duration: 1400, essential: true });
  }, [flyTo]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
