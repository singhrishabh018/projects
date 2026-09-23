import unittest

from stock_sync import payload

EVENT = {"event_id": "e1", "sku": "SKU-1", "brand": "b1", "location": "W12",
         "on_hand": 7, "reserved": 2, "ts": 1767225600000,
         "restock_date": 1767268800000}  # 2026-01-01T12:00:00Z


class HiddenRestockTest(unittest.TestCase):
    def test_restock_eta_name_and_format(self):
        item = payload.build(EVENT)
        self.assertEqual(item.get("restock_eta"), "2026-01-01")
        self.assertNotIn("restock_date", item)

    def test_null_restock_date_sends_nothing_wrong(self):
        item = payload.build(dict(EVENT, restock_date=None))
        self.assertIn(item.get("restock_eta"), (None,))
        self.assertNotIn("restock_date", item)


if __name__ == "__main__":
    unittest.main()
