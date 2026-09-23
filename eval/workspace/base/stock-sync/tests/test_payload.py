import unittest

from stock_sync import payload

EVENT = {"event_id": "e1", "sku": "SKU-1", "brand": "b1", "location": "W12",
         "on_hand": 7, "reserved": 2, "ts": 1767225600000}


class PayloadTest(unittest.TestCase):
    def test_qty_is_on_hand_minus_reserved(self):
        self.assertEqual(payload.build(EVENT)["qty"], 5)

    def test_qty_never_negative(self):
        self.assertEqual(payload.build(dict(EVENT, reserved=9))["qty"], 0)

    def test_updated_at_is_iso(self):
        self.assertEqual(payload.build(EVENT)["updated_at"], "2026-01-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
