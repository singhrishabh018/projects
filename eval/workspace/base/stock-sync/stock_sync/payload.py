"""Builds the partner inventory item from a stock.changed event."""
from datetime import datetime, timezone


def build(event):
    return {
        "sku": event["sku"],
        "qty": max(event["on_hand"] - event["reserved"], 0),
        "updated_at": datetime.fromtimestamp(event["ts"] / 1000, tz=timezone.utc).isoformat(),
    }
