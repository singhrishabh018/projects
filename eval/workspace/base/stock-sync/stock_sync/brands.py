"""Brand attributes from the nightly warehouse export (brands.csv).

Columns: brand_id, name, is_searchable, fulfillment_type
"""
import csv

from . import config

_brands = None


def load(path=None):
    global _brands
    with open(path or config.BRANDS_CSV, newline="") as f:
        _brands = {row["brand_id"]: row for row in csv.DictReader(f)}
    return _brands


def get(brand_id):
    if _brands is None:
        load()
    return _brands.get(brand_id)


def is_searchable(brand_id):
    row = get(brand_id)
    return bool(row) and row["is_searchable"] == "1"


def name(brand_id):
    row = get(brand_id)
    return row["name"] if row else brand_id
