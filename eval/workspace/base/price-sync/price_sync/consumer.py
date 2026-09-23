"""One price.changed event in, one partner price call out (eligible brands only)."""
import logging

from . import eligibility, partner

log = logging.getLogger(__name__)


def handle(event, send=partner.send_price):
    if not eligibility.is_eligible(event["brand"]):
        log.debug("brand %s not eligible, skipping %s", event["brand"], event["sku"])
        return False
    send({"sku": event["sku"], "price": event["price"], "currency": event["currency"]})
    return True
