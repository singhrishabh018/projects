import json
import logging
import urllib.request

from . import config

log = logging.getLogger(__name__)


def send_price(item, opener=urllib.request.urlopen):
    req = urllib.request.Request(
        config.PARTNER_BASE_URL.rstrip("/") + "/v2/prices",
        data=json.dumps({"items": [item]}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {config.PARTNER_TOKEN}",
                 "Content-Type": "application/json"},
    )
    with opener(req, timeout=10) as resp:
        return resp.status


def log_startup():
    log.info("price-sync partner target %s, token %s", config.PARTNER_BASE_URL, config.PARTNER_TOKEN)
