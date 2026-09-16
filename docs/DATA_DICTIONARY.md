# Ignite Data Dictionary & Column Mapping Specifications

**Project**: Ignite (PS20)  
**Document**: `docs/DATA_DICTIONARY.md`  
**Phase**: Phase 2B.6 Official EM-DAT Dataset Integration  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Overview
This document specifies the feature schemas, column mappings, data types, physical units, and missingness rules across all primary data sources integrated into Project Ignite.

---

## 2. Official EM-DAT Column Mapping Table `[VERIFIED]`

Mapping from raw official EM-DAT Excel columns (`EM-DAT Data` sheet) to PS20 canonical fields in `emdat_normalized.parquet`:

| Official EM-DAT Excel Column Name | PS20 Canonical Field Name | Target Data Type | Physical Unit | Missingness Behavior | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DisNo.` | `emdat_disno` / `source_record_id` | String | Key | **0% Null** | Unique EM-DAT disaster identifier |
| `Disaster Group` | `disaster_group` | Categorical | N/A | Preserved | Natural vs Technological |
| `Disaster Subgroup` | `disaster_subgroup` | Categorical | N/A | Preserved | Geophysical, Hydrological, etc. |
| `Disaster Type` | `disaster_type` | Categorical | N/A | Preserved | Flood, Earthquake, Storm, etc. |
| `Disaster Subtype` | `disaster_subtype` | Categorical | N/A | Preserved | Flash flood, Ground movement, etc. |
| `Event Name` | `event_name` | String | Name | Preserved | Named storm or event title |
| `ISO` | `iso3` | String | ISO3 Key | Preserved | Country 3-letter code |
| `Country` | `country` | String | Name | Preserved | Country name |
| `Region` | `region` | String | Name | Preserved | UN Region |
| `Subregion` | `subregion` | String | Name | Preserved | UN Subregion |
| `Location` | `location_text` | String | Text | Preserved | Subnational location description |
| `Latitude` | `latitude` | Float | Degrees | Preserved | Event centroid latitude |
| `Longitude` | `longitude` | Float | Degrees | Preserved | Event centroid longitude |
| `Start Year` | `start_year` | Integer | Year | Preserved | Event start year |
| `Start Month` | `start_month` | Float / Int | Month (1-12)| Preserved | Event start month |
| `Start Day` | `start_day` | Float / Int | Day (1-31) | Preserved | Event start day |
| `End Year` | `end_year` | Integer | Year | Preserved | Event end year |
| `End Month` | `end_month` | Float / Int | Month (1-12)| Preserved | Event end month |
| `End Day` | `end_day` | Float / Int | Day (1-31) | Preserved | Event end day |
| `Total Deaths` | `total_deaths` | Float / Int | Count | **Preserved NaN** | Verified total direct deaths |
| `No. Injured` | `no_injured` | Float / Int | Count | **Preserved NaN** | Total injured count |
| `No. Affected` | `no_affected` | Float / Int | Count | **Preserved NaN** | Population requiring assistance |
| `No. Homeless` | `no_homeless` | Float / Int | Count | **Preserved NaN** | Homeless population count |
| `Total Affected` | `total_affected` | Float / Int | Count | **Preserved NaN** | Total affected population |
| `Total Damage ('000 US$)` | `total_damage_usd_thousands` | Float | $1,000 USD | **Preserved NaN** | Estimated direct damage |
| `Total Damage, Adjusted ('000 US$)`| `total_damage_adjusted_usd_thousands` | Float | $1,000 USD | **Preserved NaN** | CPI-adjusted economic damage |
| `GADM Admin Units` | `gadm_admin_units` | JSON String | JSON | Preserved | Subnational GADM boundary keys |

> [!CAUTION]
> **Strict Null Preservation Rule**: Under no circumstances may missing values in `total_deaths`, `no_injured`, `total_affected`, or `total_damage_usd_thousands` be zero-imputed during ingestion or normalization. Missing values MUST remain `NaN` / `None`.
