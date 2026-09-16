# Dataset Empirical Validation Report

**Project**: Ignite (PS20)  
**Document**: `docs/DATASET_VALIDATION_REPORT.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Overview
This document records empirical validation findings for all candidate data sources evaluated during Phase 2A.

---

## 2. Source-by-Source Empirical Audit Catalog

### 2.1 Source: USGS Earthquake API `[EMPIRICAL]`
- **Dataset**: FDSNWS Seismic Event Service
- **Provider**: United States Geological Survey (USGS)
- **Access Method**: REST API (`https://earthquake.usgs.gov/fdsnws/event/1/query`)
- **Credential Requirement**: None (Open Access)
- **Geographic Coverage**: Global
- **Temporal Coverage**: Historical (1900–Present) to Real-Time
- **Spatial Resolution**: Point (`latitude`, `longitude`, `depth_km`)
- **Temporal Resolution**: Real-Time (Millisecond ISO8601 UTC)
- **Primary Key**: `id` (e.g. `us7000m123`)
- **Event Identifier**: `id`
- **Important Fields**: `mag`, `place`, `time`, `geometry.coordinates`, `pga`
- **Target-Related Fields**: None (Physical hazard predictor signal)
- **Feature-Related Fields**: `magnitude`, `depth_km`, `pga_g`, `event_time`
- **Measured Null Rate**: 0.0% nulls across magnitude, place, time, coordinates
- **Measured Duplicates**: 0 duplicates in 500 fetched records
- **Update Latency**: < 15 Minutes
- **Revision Behavior**: Minor magnitude adjustments within 24 hours
- **Licensing**: Public Domain (US Government)
- **Actual Sample Size**: 500 records fetched ($Mw \ge 4.5$, Aug 19–Sep 15, 2026)
- **Usable Sample Size**: 500 records (100% usable)
- **Status**: `[VERIFIED]` Open Access & Fully Accessible

### 2.2 Source: GDACS Disaster Alert API `[EMPIRICAL]`
- **Dataset**: Global Disaster Alert and Coordination System RSS Feed
- **Provider**: European Commission JRC / UN OCHA
- **Access Method**: RSS XML / JSON API (`https://www.gdacs.org/xml/rss.xml`)
- **Credential Requirement**: None (Open Access)
- **Geographic Coverage**: Global
- **Temporal Coverage**: Real-Time & 30-day active alerts
- **Spatial Resolution**: Point / Country Polygon
- **Temporal Resolution**: Daily Alerts
- **Primary Key**: `link` / GUID
- **Event Identifier**: `eventtype` + `eventid`
- **Important Fields**: `title`, `eventtype`, `alertlevel`, `country`, `georss:point`
- **Target-Related Fields**: `severity` text descriptors
- **Feature-Related Fields**: `event_type`, `alert_level`, `pub_date`, `point`
- **Measured Null Rate**: 0.0% nulls for event_type/point; 0.81% nulls for country
- **Measured Duplicates**: 0 duplicates in 246 fetched alerts
- **Update Latency**: 3 to 24 Hours
- **Revision Behavior**: Alert level upgraded from Green $\rightarrow$ Orange $\rightarrow$ Red as crisis evolves
- **Licensing**: Open Access / UN OCHA
- **Actual Sample Size**: 246 active alerts (213 Wildfires, 15 Floods, 13 Droughts, 3 Cyclones, 2 Earthquakes)
- **Usable Sample Size**: 246 records (100% usable)
- **Status**: `[VERIFIED]` Open Access & Fully Accessible

### 2.3 Source: ACLED (Armed Conflict Location & Event Data) `[OFFICIAL DOCUMENTATION]`
- **Dataset**: ACLED Conflict & Political Violence API
- **Provider**: ACLED Project
- **Access Method**: REST API (`https://api.acleddata.com/acled/read`)
- **Credential Requirement**: User Email + API Key (`[BLOCKED — CREDENTIAL REQUIRED]`)
- **Geographic Coverage**: Global (200+ countries)
- **Temporal Coverage**: 1997–Present (Weekly updates)
- **Spatial Resolution**: Point (Lat/Lon) / ADM1 / ADM2
- **Temporal Resolution**: Daily Events / Weekly Data Releases
- **Primary Key**: `event_id_cntr`
- **Important Fields**: `event_date`, `event_type`, `sub_event_type`, `fatalities`, `admin2`, `latitude`, `longitude`
- **Target-Related Fields**: `fatalities` (Used in derived severity target)
- **Feature-Related Fields**: `events_count`, `fatalities_sum`, `event_type_distribution`
- **Update Latency**: 7 to 14 Days
- **Revision Behavior**: Retroactive edits occur up to 90 days post-event
- **Licensing**: Free for non-commercial research; API key required
- **Status**: `[BLOCKED — CREDENTIAL REQUIRED]` Validated via official documentation

### 2.4 Source: IPC Food Security Classification `[OFFICIAL DOCUMENTATION]`
- **Dataset**: IPC Public API / FEWS NET Data Portal
- **Provider**: Integrated Food Security Phase Classification (IPC)
- **Access Method**: REST API (`https://api.ipcinfo.org/`)
- **Credential Requirement**: API Key for programmatic bulk export (`[BLOCKED — CREDENTIAL REQUIRED]`)
- **Geographic Coverage**: 45+ Crisis-affected Countries
- **Temporal Coverage**: 2004–Present (Quarterly/Seasonal Surveys)
- **Spatial Resolution**: ADM1 / ADM2 / Custom IPC Zones
- **Temporal Resolution**: Quarterly / Bi-annual
- **Primary Key**: `country_code` + `adm2_pcode` + `period_start`
- **Important Fields**: `phase_class` (1-5), `pop_phase1` to `pop_phase5`
- **Target-Related Fields**: `phase_class` (Vulnerability context)
- **Feature-Related Fields**: `pop_phase3_plus_ratio`
- **Update Latency**: 30 to 90 Days post-survey
- **Licensing**: Open Access / Attribution Required
- **Status**: `[BLOCKED — CREDENTIAL REQUIRED]` Validated via official documentation

### 2.5 Source: UN OCHA COD-AB (Common Operational Datasets - Boundaries) `[VERIFIED]`
- **Dataset**: Subnational Administrative Boundary P-codes
- **Provider**: UN OCHA / Humanitarian Data Exchange (HDX)
- **Access Method**: CKAN API / Direct Download
- **Credential Requirement**: None
- **Geographic Coverage**: Global
- **Temporal Coverage**: Annual / Periodic Boundary Releases
- **Spatial Resolution**: ADM0, ADM1, ADM2 Polygons
- **Primary Key**: `ADM2_PCODE` (e.g. `SDN001002`)
- **Status**: `[VERIFIED]` Standard Spatial Backbone
