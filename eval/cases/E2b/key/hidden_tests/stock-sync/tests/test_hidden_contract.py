import unittest

from stock_sync import payload

EVENT = {"event_id": "e1", "sku": "SKU-1", "brand": "b1", "location": "W12",
         "on_hand": 7, "reserved": 2, "ts": 1767225600000}


class HiddenContractTest(unittest.TestCase):
    def test_partner_field_is_still_qty(self):
        item = payload.build(EVENT)
        self.assertEqual(item.get("qty"), 5)


if __name__ == "__main__":
    unittest.main()
