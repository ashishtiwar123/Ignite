# Official EM-DAT Real Dataset Validation Report

**Project**: Ignite (PS20 — Multi-Hazard Disaster & Emergency Response System)  
**Document**: `docs/EMDAT_REAL_DATASET_VALIDATION.md`  
**Phase**: Phase 2B.6 — Official EM-DAT Dataset Integration  
**Status**: APPROVED & COMPLETE  
**Provenance**: `[VERIFIED MANUAL DOWNLOAD]`  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Download Metadata

This document records the empirical validation and ingestion findings for the official manually downloaded **Public EM-DAT Custom Export Dataset**.

### 1.1 Download Provenance & Checksum `[VERIFIED MANUAL DOWNLOAD]`
- **Source**: Public EM-DAT Platform (CRED / Université catholique de Louvain)
- **Local File Path**: [`ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx)
- **File Size**: **6,190,151 bytes (~5.9 MB)**
- **SHA256 Checksum**: `7f1ce93f5f1b5a16fc77f07d58da4aecd1851b95a0ebbde573d144eca23bf107`
- **Retrieval Date**: 2026-09-16
- **Workbook Sheets**: `['EM-DAT Data', 'EM-DAT Info']`
- **Primary Data Sheet**: `'EM-DAT Data'`
- **Actual Physical Record Count**: **16,764 records**
- **Column Count**: **47 columns**
- **Temporal Coverage**: **2000 to 2025** (25-year historical baseline)
- **Geographic Coverage**: **223 countries and territories**

---

## 2. Answers to Section 19 Governance Audit Questions

| Audit Question | Empirical Answer / Finding | Evidence / Status |
| :--- | :--- | :--- |
| **A. Does official file exist?** | **YES.** Physical file present in workspace repository. | `[EMPIRICAL]` `os.path.exists` |
| **B. Exact file size?** | **6,190,151 bytes (5.9 MB)**. | `[EMPIRICAL]` `os.path.getsize` |
| **C. Exact SHA256?** | `7f1ce93f5f1b5a16fc77f07d58da4aecd1851b95a0ebbde573d144eca23bf107` | `[EMPIRICAL]` `hashlib.sha256` |
| **D. Actual number of records?** | **16,764 records** in `'EM-DAT Data'` sheet. | `[EMPIRICAL]` `len(df)` |
| **E. Actual date range?** | **2000 to 2025** (Start Year min: 2000, max: 2025). | `[EMPIRICAL]` `df['Start Year'].min()/max()` |
| **F. Number of countries?** | **223 unique countries/territories**. | `[EMPIRICAL]` `df['Country'].nunique()` |
| **G. Number of disaster types?** | **31 distinct disaster types** across Natural and Technological groups. | `[EMPIRICAL]` `df['Disaster Type'].value_counts()` |
| **H. Records with observed deaths?** | **13,494 records** (80.5% coverage). | `[EMPIRICAL]` `df['Total Deaths'].notnull().sum()` |
| **I. Records with observed injured?** | **6,266 records** (37.4% coverage). | `[EMPIRICAL]` `df['No. Injured'].notnull().sum()` |
| **J. Records with observed affected?** | **7,782 records** (46.4% coverage). | `[EMPIRICAL]` `df['Total Affected'].notnull().sum()` |
| **K. Records with observed damage?** | **722 records** (4.3% coverage). | `[EMPIRICAL]` `df['Total Damage'].notnull().sum()` |
| **L. Duplicate event IDs?** | **0 duplicate IDs** (16,764 unique `DisNo.` keys). | `[EMPIRICAL]` `df['DisNo.'].nunique()` |
| **M. Primary disaster-outcome suitability?** | **YES.** Highly suitable as primary historical ground-truth loss repository. | `[VERIFIED]` Architecture Standard |
| **N. Remaining limitations?** | Subnational P-code granularity is partial (`Admin Units` field present in text JSON format in 30% of records). | `[INFERRED]` Field inspection |

---

## 3. Disaster Type Distribution & PS20 Taxonomy Mapping

`[EMPIRICAL]` Breakdown of top EM-DAT disaster categories and mapping to PS20 canonical taxonomy:

| EM-DAT Disaster Type | Raw Record Count | Percentage % | PS20 Canonical Hazard Mapping | Mapping Status |
| :--- | :---: | :---: | :--- | :--- |
| **Flood** | 4,247 | 25.33% | `FLOOD` | `[VERIFIED]` Direct Match |
| **Storm** | 2,850 | 17.00% | `CYCLONE` | `[VERIFIED]` Direct Match |
| **Road (Technological)** | 2,238 | 13.35% | `ACCIDENT` / Non-Hazard | `[EXCLUDED FROM NATURAL ML]` |
| **Water (Technological)** | 1,174 | 7.00% | `ACCIDENT` / Non-Hazard | `[EXCLUDED FROM NATURAL ML]` |
| **Epidemic** | 893 | 5.33% | `EPIDEMIC` / Health Surge | `[CONTEXT-ONLY]` |
| **Earthquake** | 693 | 4.13% | `EARTHQUAKE` | `[VERIFIED]` Direct Match |
| **Extreme temperature** | 606 | 3.61% | `EXTREME_WEATHER` | `[VERIFIED]` Direct Match |
| **Mass movement (wet)** | 493 | 2.94% | `LANDSLIDE` | `[VERIFIED]` Direct Match |
| **Drought** | 424 | 2.53% | `DROUGHT` | `[VERIFIED]` Direct Match |
| **Wildfire** | 344 | 2.05% | `WILDFIRE` | `[VERIFIED]` Direct Match |
| **Volcanic activity** | 133 | 0.79% | `VOLCANO` | `[VERIFIED]` Direct Match |
| **Other / Technological** | 2,670 | 15.93% | Various | `[FILTERED BY DISASTER GROUP]` |

---

## 4. Legacy vs. Primary EM-DAT Source Comparison

| Dimension | Legacy Dataset (`raw_emdat.json`) | Primary Dataset (`public_emdat_custom_request...xlsx`) |
| :--- | :--- | :--- |
| **Source Provenance** | `[STATIC DATA]` Hardcoded Python array | `[VERIFIED MANUAL DOWNLOAD]` Official Export |
| **Record Count** | 18 benchmark events | **16,764 official records** |
| **File Format** | JSON | **Excel (.xlsx)** $\rightarrow$ **Parquet (.parquet)** |
| **Status Designation** | `LEGACY_STATIC_EMDAT` (Retained for audit) | `PRIMARY_EMDAT_SOURCE` (Active Primary Source) |

---

## 5. Automated Unit Test Verification `[EMPIRICAL]`

`[EMPIRICAL]` Execution of `pytest ml/tests/test_emdat_ingestion.py -v`:
- `test_emdat_excel_file_exists`: **PASSED** (File size 6.19 MB > 5 MB).
- `test_emdat_sheet_structure`: **PASSED** (Sheet `'EM-DAT Data'` present, 16,764 rows).
- `test_normalized_parquet_exists`: **PASSED** (16,764 records normalized, `source_dataset == EM-DAT`).
- `test_null_preservation_not_converted_to_zero`: **PASSED** (3,270 missing deaths preserved as `NaN`).
- `test_temporal_date_validity`: **PASSED** (Start Year $\ge 2000$, Start Year $\le$ End Year).
- `test_raw_excel_unmodified`: **PASSED** (SHA256 checksum verified).
- **Result: 6 PASSED in 21.20s**.
