import pytest
import os
import hashlib
import pandas as pd

EXCEL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx"
PARQUET_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet"

def test_emdat_excel_file_exists():
    assert os.path.exists(EXCEL_PATH), f"Official EM-DAT Excel file must exist at {EXCEL_PATH}"
    size = os.path.getsize(EXCEL_PATH)
    assert size > 5000000, f"Expected Excel file size > 5MB, found {size} bytes"

def test_emdat_sheet_structure():
    excel_file = pd.ExcelFile(EXCEL_PATH)
    assert "EM-DAT Data" in excel_file.sheet_names, "Sheet 'EM-DAT Data' must exist in workbook"
    df = pd.read_excel(EXCEL_PATH, sheet_name="EM-DAT Data")
    assert len(df) == 16764, f"Expected exactly 16,764 records, found {len(df)}"
    assert "DisNo." in df.columns, "Primary key column 'DisNo.' must exist"

def test_normalized_parquet_exists():
    assert os.path.exists(PARQUET_PATH), f"Normalized Parquet dataset must exist at {PARQUET_PATH}"
    df = pd.read_parquet(PARQUET_PATH)
    assert len(df) == 16764, f"Expected 16,764 normalized records, found {len(df)}"
    assert (df["source_dataset"] == "EM-DAT").all()
    assert df["source_record_id"].isnull().sum() == 0, "Source record ID must not be null"

def test_null_preservation_not_converted_to_zero():
    df = pd.read_parquet(PARQUET_PATH)
    # Assert missing total_deaths contains actual NaNs and is not zero-imputed
    null_deaths_count = df["total_deaths"].isnull().sum()
    assert null_deaths_count > 0, "Missing total_deaths must be preserved as NaN"
    assert null_deaths_count == 16764 - 13494, f"Expected 3270 missing deaths, found {null_deaths_count}"

def test_temporal_date_validity():
    df = pd.read_parquet(PARQUET_PATH)
    valid_years = df[(df["start_year"].notnull()) & (df["end_year"].notnull())]
    assert (valid_years["start_year"] <= valid_years["end_year"]).all(), "Start year must be <= end year"
    assert (valid_years["start_year"] >= 2000).all(), "Start year must be >= 2000"
    assert (valid_years["end_year"] <= 2026).all(), "End year must be <= 2026"

def test_raw_excel_unmodified():
    # Verify exact SHA256 checksum
    h = hashlib.sha256()
    with open(EXCEL_PATH, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    expected_sha256 = "7f1ce93f5f1b5a16fc77f07d58da4aecd1851b95a0ebbde573d144eca23bf107"
    assert h.hexdigest() == expected_sha256, "Raw Excel file must remain unmodified"
