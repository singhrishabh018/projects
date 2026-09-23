"""Which brands may be sent to the partner: the warehouse's eligible_brands export.

Loaded once when the process starts. The export is regenerated nightly by the warehouse.
"""
import csv

from . import config

_eligible = None


def load(path=None):
    global _eligible
    with open(path or config.ELIGIBLE_BRANDS_CSV, newline="") as f:
        _eligible = {row["brand_id"] for row in csv.DictReader(f)}
    return _eligible


def is_eligible(brand_id):
    if _eligible is None:
        load()
    return brand_id in _eligible
