"""Main loop: one stock.changed event in, one partner inventory call out."""
import logging

from . import brands, config, payload
from .broker import Broker
from .dedup import SentLog
from .partner_client import PartnerClient

log = logging.getLogger(__name__)


def handle(event, client, sent_log, broker):
    if sent_log.seen(event["event_id"]):
        log.info("skipping already-sent event %s", event["event_id"])
        return
    item = payload.build(event)
    client.send_inventory([item])
    sent_log.mark(event["event_id"])
    broker.publish("stock.sent", item)
    log.info("Stock update recieved and sent for %s (%s)", event["sku"], brands.name(event["brand"]))


def run(broker_client):
    broker = Broker(broker_client)
    client = PartnerClient()
    sent_log = SentLog(config.SENT_LOG_PATH)
    for message in broker.subscribe("stock.changed", group=config.CONSUMER_GROUP):
        handle(message.value, client, sent_log, broker)
        broker.commit(message)
