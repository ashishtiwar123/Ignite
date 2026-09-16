# Multi-Hazard Feature Expansion Plan & Roadmap
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/MULTI_HAZARD_FEATURE_EXPANSION_PLAN.md`  
**Phase**: Phase 2C.2  
**Status**: APPROVED  
**Date**: 2026-09-16  

---

## 1. Multi-Hazard Data Expansion Roadmap

| Hazard Type | Physical Hazard Data Source | Required Physical Features | Exposure / Context Source | Current Readiness Status | Next Action Required |
|---|---|---|---|---|---|
| **Earthquake** | USGS GeoJSON API | Magnitude, Depth, PGA, Lat/Lon | WorldBank Pop Density / GHSL | **READY FOR MODELING** | Feature-Enriched V5 complete |
| **Tropical Cyclone** | NOAA IBTrACS | Max Wind, Min Pressure, Storm Category | WorldBank Pop Density / Coastal Buffer | **READY FOR MODELING** | Feature-Enriched V5 complete |
| **Flood** | Copernicus GloFAS / ERA5 Reanalysis | Peak Discharge ($m^3/s$), 7-Day Rainfall Accumulation | WorldBank Pop Density / Floodplain Footprint | **DATA GAPS** | CDS API batch retrieval pipeline required |
| **Wildfire** | NASA FIRMS (MODIS/VIIRS) | Fire Radiative Power (FRP), Burned Area ($ha$) | WorldBank Pop Density / Wildland-Urban Interface | **DATA GAPS** | FIRMS Archive download pipeline required |
| **Landslide** | NASA Global Landslide Catalog / USGS | Rainfall Trigger, Slope Stability, Elevation | WorldBank Pop Density / Slope Footprint | **DATA GAPS** | GLC spatial join pipeline required |
| **Drought** | NOAA SPEI / CHIRPS | SPEI Index, Precipitation Anomaly | WorldBank Agrarian Population Density | **DATA GAPS** | CHIRPS raster extraction pipeline required |
| **Extreme Temp** | ERA5 Global Heatwave Reanalysis | Max Temp Anomaly ($^\circ C$), Heat Duration | WorldBank Urban Pop Density | **DATA GAPS** | ERA5 heatwave index pipeline required |
