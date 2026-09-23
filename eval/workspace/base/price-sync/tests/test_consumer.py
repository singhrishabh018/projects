import os
import tempfile
import unittest

from price_sync import consumer, eligibility


class ConsumerTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join(tempfile.mkdtemp(), "eligible_brands.csv")
        with open(path, "w") as f:
            f.write("brand_id\nb1\n")
        eligibility.load(path)
        self.sent = []

    def test_eligible_brand_is_sent(self):
        self.assertTrue(consumer.handle({"sku": "S1", "brand": "b1", "price": "9.99",
                                         "currency": "EUR"}, send=self.sent.append))
        self.assertEqual(self.sent[0]["sku"], "S1")

    def test_ineligible_brand_is_skipped(self):
        self.assertFalse(consumer.handle({"sku": "S2", "brand": "b9", "price": "1.00",
                                          "currency": "EUR"}, send=self.sent.append))
        self.assertEqual(self.sent, [])


if __name__ == "__main__":
    unittest.main()
