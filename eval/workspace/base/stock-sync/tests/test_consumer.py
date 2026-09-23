import os
import tempfile
import unittest

from stock_sync import brands, consumer
from stock_sync.dedup import SentLog
from stock_sync.partner_client import PartnerClient
from tests.fake_partner import FakePartner

EVENT = {"event_id": "e1", "sku": "SKU-1", "brand": "b1", "location": "W12",
         "on_hand": 7, "reserved": 2, "ts": 1767225600000}


class FakeBroker:
    def __init__(self):
        self.published = []

    def publish(self, topic, value):
        self.published.append((topic, value))


class ConsumerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        csv_path = os.path.join(self.tmp, "brands.csv")
        with open(csv_path, "w") as f:
            f.write("brand_id,name,is_searchable,fulfillment_type\nb1,Acme,1,ship\n")
        brands.load(csv_path)
        self.partner = FakePartner()
        self.client = PartnerClient(base_url="https://p.test", token="t", opener=self.partner)
        self.sent_log = SentLog(os.path.join(self.tmp, "sent.db"))
        self.broker = FakeBroker()

    def test_sends_one_item_per_event(self):
        consumer.handle(EVENT, self.client, self.sent_log, self.broker)
        self.assertEqual(len(self.partner.requests), 1)
        self.assertEqual(self.partner.requests[0]["body"]["items"][0]["sku"], "SKU-1")

    def test_redelivered_event_not_sent_twice(self):
        consumer.handle(EVENT, self.client, self.sent_log, self.broker)
        consumer.handle(EVENT, self.client, self.sent_log, self.broker)
        self.assertEqual(len(self.partner.requests), 1)

    def test_publishes_sent_item(self):
        consumer.handle(EVENT, self.client, self.sent_log, self.broker)
        self.assertEqual(self.broker.published[0][0], "stock.sent")


if __name__ == "__main__":
    unittest.main()
