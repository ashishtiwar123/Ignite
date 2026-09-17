# PS20 Phase 6C Audit: Map Integration & Environment Configuration Fix

**Date**: September 17, 2026  
**Component**: Frontend Command Dashboard Map Integration (`DisasterMap.tsx`, `MapCanvas.tsx`, `vite.config.ts`)  
**Status**: **VERIFIED & OPERATIONAL** (Base Map Live, Production Build Clean, Null Coordinates Safely Handled)

---

## 1. Executive Summary
During manual UI verification of the PS20 Command Dashboard (`/dashboard`), the central map area was blocked by the message:
> *"Map credentials are unavailable. Reconnect Mapbox to load the live map."*

Inspection revealed a combination of configuration and code issues:
1. **Environment Scope**: Vite dev server and build run with `process.cwd()` set to `frontend/`. By default, Vite looks for `.env` files exclusively in its local directory and does not traverse to the Ignite repository root `.env`.
2. **Environment Variable Naming Mismatch**: The repository root `.env` configured the token under `VITE_MAPBOX_TOKEN`, while the frontend map component checked `VITE_MAPBOX_PUBLIC_TOKEN` and `VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN`.
3. **Runtime `ReferenceError` in Marker Placement**: In `DisasterMap.tsx`, `props.backendIncidents` was referenced inside `placeMarkers()` without `props` or `backendIncidents` being in scope, which would have thrown an unhandled `ReferenceError: props is not defined` as soon as credentials were provided.
4. **Missing Interaction Handler**: Backend incident markers did not have a click listener attached to invoke `onSelectIncident(incident)`.
5. **Coordinate Validation & Resilience**: Real incidents returned from FastAPI currently have `centroid_latitude = null` and `centroid_longitude = null`. The marker placement logic lacked strict range validation (`-90..90`, `-180..180`, `!isNaN`).

Following minimal, surgical modifications, the root `.env` is loaded safely, token compatibility is established in strict priority order, markers are safely validated, the production build succeeds without errors, and the live Mapbox Satellite base map renders in the browser.

---

## 2. Root Cause Analysis

### A. Environment Resolution
* Vite's default `envDir` is `root` (`frontend/`).
* Running `npm run dev` or `npm run build` in `frontend/` meant `loadEnv()` returned an empty key set (`[]`).
* Vite never loaded the existing root `.env`.

### B. Credential Key Discrepancy
* Root `.env` defined: `VITE_MAPBOX_TOKEN`.
* Map component code expected:
  ```ts
  const token = (import.meta.env["VITE_MAPBOX_PUBLIC_TOKEN"] ??
    import.meta.env["VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN"]) as string | undefined;
  ```
  Neither key matched the root environment definition.

### C. Component Scope Bug
* Component signature was:
  ```tsx
  export default function DisasterMap({ scenario, mode, layers, onSelectIncident }: Props)
  ```
* At marker placement (line 416):
  ```tsx
  if (props.backendIncidents && props.backendIncidents.length > 0)
  ```
  `props` was not declared, producing TypeScript error `TS2304: Cannot find name 'props'` and a fatal runtime crash upon receiving credentials.

---

## 3. Files Changed

### 1. `frontend/vite.config.ts`
* Added `envDir: path.resolve(__dirname, "..")` to Vite options forwarded via `@lovable.dev/vite-tanstack-config`.
* Preserved all existing TanStack Start plugins, SSR entry, and Tailwind/Nitro pipeline.
* Did **not** create a second `.env` file.

### 2. `frontend/src/components/dr/DisasterMap.tsx`
* **Token Compatibility**: Updated resolution order:
  1. `import.meta.env["VITE_MAPBOX_PUBLIC_TOKEN"]`
  2. `import.meta.env["VITE_MAPBOX_TOKEN"]`
  3. `import.meta.env["VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN"]`
* **Destructuring**: Correctly destructured `backendIncidents` in `DisasterMap({ scenario, mode, layers, onSelectIncident, backendIncidents }: Props)`.
* **Reactivity**: Added `backendIncidentsRef` and a `useEffect` hook listening to `[backendIncidents]` to re-trigger marker placement when live incident data arrives from the API.
* **Coordinate Validation**: Added `isValidCoordinate(lat, lng)` ensuring `typeof === 'number'`, `!isNaN()`, `-90 <= lat <= 90`, and `-180 <= lng <= 180`.
* **Click Handler**: Attached `click` event listener to backend incident markers that calls `selectRef.current({...})` to update the dashboard's `selected` incident state.
* **Fallback Discipline**: Ensured that when `backendIncidents` is provided (even if records have null coordinates), the system does not fall back to fabricated mock incidents.

### 3. `frontend/src/components/ops/MapCanvas.tsx`
* Harmonized token resolution priority to check `VITE_MAPBOX_PUBLIC_TOKEN`, `VITE_MAPBOX_TOKEN`, and `VITE_LOVABLE_CONNECTOR_MAPBOX_PUBLIC_TOKEN`.

---

## 4. Security & Credential Boundary Audit
* **Backend Secrets Shielding**: Vite strictly filters environment variables by prefix. Verified via `vite.resolveConfig()` that `GEMINI_API_KEY`, `SUPABASE_KEY` (service-role), and `SUPABASE_URL` are completely omitted from the client bundle (`resolved.env` contains only `VITE_*` keys).
* **Token Redaction**: No Mapbox token values are committed, logged, or included in any audit document.
* **Zero Second `.env`**: Maintained single source of truth in project-root `.env`.

---

## 5. Live Browser Verification Results

Browser subagent verification was performed against `http://localhost:8080/dashboard`:
* **Base Map**: Live Mapbox Satellite base map loaded cleanly centered over Kurla West (`19.0760° N, 72.8777° E`).
* **Map Canvas**: `<canvas aria-label="Map" class="mapboxgl-canvas" role="region">` active and rendered.
* **Error Banner**: The message *"Map credentials are unavailable. Reconnect Mapbox to load the live map."* is **completely eliminated**.
* **Console Logs**: Clean console connection (`[vite] connected.`). Zero Mapbox, WebGL, or JavaScript runtime errors.
* **Facility Markers**: Shelters (`S`), Hospitals (`H`), and Warehouses (`W`) markers placed and interactive.
* **Dashboard Layout**: Preserved intact without layout shifts or alterations.

---

## 6. Build & Test Verification Results

* **Frontend Production Build**:
  `npm run build --prefix frontend`
  * Rolldown client chunks compiled in 6.52s.
  * Nitro server bundle compiled in 1.38s (Cloudflare preset).
  * Exit code: `0` (Success).
* **TypeScript Check**:
  Fixed `TS2304` (`props` not defined) and `TS2345` (property string cast) in `DisasterMap.tsx`.

---

## 7. Current Data Limitation: Backend Incident Coordinates

* **Observed Reality**: Live incidents returned by the backend API (`GET /incidents`) currently have:
  ```json
  [
    {
      "incident_id": "193a4cbb-9272-4881-86dd-c267b0711233",
      "hazard_type": "Flood",
      "status": "CANDIDATE",
      "centroid_latitude": null,
      "centroid_longitude": null
    },
    {
      "incident_id": "035ba2a2-c09a-492e-a62b-c88d687a057a",
      "hazard_type": "Flood",
      "status": "NEEDS_VERIFICATION",
      "centroid_latitude": null,
      "centroid_longitude": null
    }
  ]
  ```
* **Resilience Behavior**:
  * Because `centroid_latitude` and `centroid_longitude` are `null`, the coordinate validator correctly and safely omits these markers from the map canvas.
  * The map does not crash and does not place markers at `[0, 0]`.
  * In strict compliance with guidelines, **no fake/mock coordinates were fabricated on the frontend** to force marker display.
  * When reports with real GPS coordinates are ingested and processed through the verification pipeline to establish valid incident centroids, the map will immediately render them with the interactive click and popup handlers.
