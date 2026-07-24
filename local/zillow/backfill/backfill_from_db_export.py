"""
One-off migration: merge an RDS snapshot export (Parquet files produced by
`aws rds start-export-task` for the `homes` / `price_history` tables) into the
scraper's CSV files, using the same field layout and dedup rules as
local/zillow/zillow.py.

Usage:
    cd local/zillow
    python backfill/backfill_from_db_export.py \
        --homes-parquet /path/to/public.homes/1/part-....gz.parquet \
        --price-history-parquet /path/to/public.price_history/1/part-....gz.parquet
"""
import argparse
import csv
import os
from typing import Dict, List

import pyarrow.parquet as pq

HOMES_CSV_PATH = "data/homes.csv"
HOMES_CSV_FIELDS = [
    "url", "sold_price", "raw_sold_price",
    "address_city", "address_street", "address_state", "address_zipcode",
    "date_sold", "bedrooms", "bathrooms", "sqft",
    "days_on_market", "type", "zestimate",
    "lot_size", "lot_size_unit", "tax_assessment", "zpid",
]
HOMES_DEDUP_FIELDS = ("address_city", "address_street", "address_state", "date_sold")

PRICE_HISTORY_CSV_PATH = "data/price_history.csv"
PRICE_HISTORY_CSV_FIELDS = ["zpid", "price", "time", "date", "price_per_sq_ft", "price_change_rate", "event"]
PRICE_HISTORY_DEDUP_FIELDS = ("zpid", "time", "event")


def _csv_str(value) -> str:
    return "" if value is None else str(value)


def _read_csv_rows(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_csv_rows(path: str, fieldnames: List[str], rows: List[Dict]):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def merge(parquet_path: str, csv_path: str, fieldnames: List[str], dedup_fields):
    export_rows = pq.read_table(parquet_path).to_pylist()
    rows = _read_csv_rows(csv_path)
    existing_keys = {tuple(row.get(f, "") for f in dedup_fields) for row in rows}

    added = 0
    for record in export_rows:
        row = {field: _csv_str(record.get(field)) for field in fieldnames}
        key = tuple(row[f] for f in dedup_fields)
        if key in existing_keys:
            continue
        rows.append(row)
        existing_keys.add(key)
        added += 1

    if added:
        _write_csv_rows(csv_path, fieldnames, rows)
    print(f"{csv_path}: {len(export_rows)} rows in export, {added} new, {len(rows)} total after merge")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--homes-parquet", required=True)
    parser.add_argument("--price-history-parquet", required=True)
    args = parser.parse_args()

    merge(args.homes_parquet, HOMES_CSV_PATH, HOMES_CSV_FIELDS, HOMES_DEDUP_FIELDS)
    merge(args.price_history_parquet, PRICE_HISTORY_CSV_PATH, PRICE_HISTORY_CSV_FIELDS, PRICE_HISTORY_DEDUP_FIELDS)
