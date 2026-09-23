"""Finds the new reset function wherever it was added and checks the request it makes."""
import importlib
import inspect
import pkgutil
import unittest

import stock_sync
from stock_sync.partner_client import PartnerClient
from tests.fake_partner import FakePartner


def _call_reset(client, code):
    for name, member in inspect.getmembers(PartnerClient, inspect.isfunction):
        if "reset" in name.lower():
            return getattr(client, name)(code)
    for mod in pkgutil.iter_modules(stock_sync.__path__):
        m = importlib.import_module(f"stock_sync.{mod.name}")
        for name, fn in inspect.getmembers(m, inspect.isfunction):
            if "reset" in name.lower() and fn.__module__ == m.__name__:
                params = list(inspect.signature(fn).parameters)
                if len(params) >= 2:
                    try:
                        return fn(client, code)
                    except TypeError:
                        return fn(code, client)
                return fn(code, client=client)
    raise AssertionError("no reset function found")


class HiddenResetTest(unittest.TestCase):
    def test_reset_posts_to_location(self):
        fake = FakePartner()
        client = PartnerClient(base_url="https://p.test", token="t", opener=fake)
        _call_reset(client, "W12")
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(fake.requests[0]["method"], "POST")
        self.assertEqual(fake.requests[0]["url"], "https://p.test/v2/locations/W12/reset")


if __name__ == "__main__":
    unittest.main()
