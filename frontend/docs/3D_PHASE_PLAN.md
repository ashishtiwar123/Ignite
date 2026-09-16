# ResQAI Frontend — Three.js 3D Disaster Visualization Roadmap

This document outlines the phased implementation plan for rendering dynamic **Three.js** 3D visual effects directly onto **Mapbox GL JS** 3D terrain and maps.

---

## Mapbox 3D Basemap & Style Configuration

### Recommended Mapbox Styles
1. **3D Dusk / Dark Mode (Default Command View)**: `mapbox://styles/mapbox/dark-v11`
   - Paired with Mapbox 3D terrain (`mapbox-terrain-dem-v1`) and fill-extrusion 3D building layers.
   - Provides high contrast for glowing fire particles, water lighting, and seismic rings.
2. **3D Satellite View**: `mapbox://styles/mapbox/satellite-streets-v12`
   - Photorealistic high-resolution aerial imagery for realistic flood inundation and rain overlays.

---

## Phased Implementation Plan

### Phase 1: Core Three.js + Mapbox Integration Harness
- **Goal**: Establish the WebGL matrix bridge between Mapbox GL JS and Three.js.
- **Tasks**:
  - Install `three` and `@types/three`.
  - Create standard `CustomLayerInterface` inside `three-effect.ts`.
  - Map coordinates using `mapboxgl.MercatorCoordinate.fromLngLat()`.
  - Sync Three.js `PerspectiveCamera` with Mapbox camera matrix every frame.

---

### Phase 2: 🌊 Flood — Flowing Water Simulation
- **Goal**: Render dynamic 3D flowing water over the flood zone footprint.
- **Visual Features**:
  - Animated 3D plane geometry aligned to terrain height.
  - Custom vertex/fragment shader with animated normal map wave displacement.
  - Transparent blue ocean/river depth tinting with light reflections.

---

### Phase 3: 🔥 Fire — Dynamic Particle Flames & Rising Smoke
- **Goal**: Render animated 3D fire epicenters with volumetric smoke columns.
- **Visual Features**:
  - 3D particle emitter system at incident coordinates.
  - Textured flame particles with additive blending and color transition (yellow → orange → red).
  - Volumetric dark grey smoke particles rising upward with wind drift.
  - PointLight illumination casting warm fire glow onto surrounding 3D buildings.

---

### Phase 4: 🌀 Cyclone & Storms — Cloud Vortex & Wind Fields
- **Goal**: Render atmospheric clouds and storm vortices over the affected region.
- **Visual Features**:
  - 3D rotating spiral cloud disc mesh positioned at altitude.
  - Swirling volumetric particle clouds with speed controls based on wind velocity.
  - Atmospheric dark storm tint and lightning flash bursts.

---

### Phase 5: ⚡ Earthquake & Heavy Rainfall
- **Goal**: Render 3D epicenter shockwaves and rain particle downpours.
- **Visual Features**:
  - **Earthquake**: Expanding concentric 3D rings pulse outwards on terrain with fading alpha.
  - **Heavy Rain**: Vertical streak particle system simulating high-velocity rainfall falling over the zone.
