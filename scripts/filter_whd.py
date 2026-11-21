#!/usr/bin/env python3
"""Filter the DOL Wage and Hour Division (WHD) compliance-action file.

Source (official DOL open data portal, dataset WHD/enforcement, the successor
of the enforcedata.dol.gov "whd_whisard" catalog entry):
  https://data.dol.gov/data-catalog/WHD/enforcement/WHD_enforcement.zip

Keeps one row per case where:
  - NAIC_CD starts with 5613 (employment services, incl. 561311, 561312,
    561320, 561330 and the 4/5-digit and legacy 561310 forms),
  - BW_ATP_AMT (back wages) >= 10000,
  - FINDINGS_END_DATE is in 2015 or later.
Sorted by back wages, descending. Nothing is aggregated.

Usage (run isolated, from any directory):
  python3 -I filter_whd.py [input.zip|input.csv] [output.csv] [source data date]
"""
import csv
import io
import math
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "raw", "WHD_enforcement.zip")  # download it first; it is not in the repository
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "data", "staffing_wage_violations.csv")
SOURCE_URL = "https://data.dol.gov/data-catalog/WHD/enforcement/WHD_enforcement.zip"

NAICS_PREFIX = "5613"
MIN_BACK_WAGES = 10000.0
MIN_END_YEAR = 2015

OUT_COLUMNS = [
    "name", "trade_name", "city", "state", "naics_code", "naics_description",
    "findings_start_date", "findings_end_date", "back_wages",
    "employees_owed", "flsa_violations", "case_id", "source_url", "source_data_date",
]


def day(value):
    """'2016-02-06 00:00:00+00:00' -> '2016-02-06'. Blank or 'NaT' -> ''."""
    value = (value or "").strip()
    return "" if value in ("", "NaT") else value[:10]


def num(value):
    try:
        number = float((value or "").strip().replace("$", "").replace(",", ""))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def open_text(path):
    if path.lower().endswith(".zip"):
        z = zipfile.ZipFile(path)
        raw = z.open(z.namelist()[0])
    else:
        raw = open(path, "rb")
    return io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IN
    dst = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    data_date = sys.argv[3] if len(sys.argv) > 3 else ""

    kept, scanned, skipped_bad = [], 0, 0
    with open_text(src) as fh:
        for row in csv.DictReader(fh):
            scanned += 1
            if not (row.get("NAIC_CD") or "").strip().startswith(NAICS_PREFIX):
                continue
            back_wages = num(row.get("BW_ATP_AMT"))
            if back_wages is None:
                skipped_bad += 1
                continue
            if back_wages < MIN_BACK_WAGES:
                continue
            end = day(row.get("FINDINGS_END_DATE"))
            if not end[:4].isdigit() or int(end[:4]) < MIN_END_YEAR:
                continue
            trade = (row.get("TRADE_NM") or "").strip()
            legal = (row.get("LEGAL_NAME") or "").strip()
            kept.append({
                "name": legal or trade,
                "trade_name": trade,
                "city": (row.get("CTY_NM") or "").strip(),
                "state": (row.get("ST_CD") or "").strip(),
                "naics_code": (row.get("NAIC_CD") or "").strip(),
                "naics_description": (row.get("NAICS_CODE_DESCRIPTION") or "").strip(),
                "findings_start_date": day(row.get("FINDINGS_START_DATE")),
                "findings_end_date": end,
                "back_wages": f"{back_wages:.2f}",
                "employees_owed": (row.get("EE_ATP_CNT") or "").strip(),
                "flsa_violations": (row.get("FLSA_VIOLTN_CNT") or "").strip(),
                "case_id": (row.get("CASE_ID") or "").strip(),
                "source_url": SOURCE_URL,
                "source_data_date": data_date,
                "_bw": back_wages,
            })

    kept.sort(key=lambda r: r["_bw"], reverse=True)
    with open(dst, "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=OUT_COLUMNS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(kept)

    print(f"scanned={scanned} kept={len(kept)} unparseable_back_wages={skipped_bad}")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
