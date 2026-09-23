import logging
import unittest

from price_sync import config, partner


class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


class HiddenTokenTest(unittest.TestCase):
    def test_startup_log_has_no_token(self):
        config.PARTNER_TOKEN = "SECRET-TOKEN-123"
        cap = Capture()
        root = logging.getLogger()
        root.addHandler(cap)
        root.setLevel(logging.DEBUG)
        try:
            if hasattr(partner, "log_startup"):
                partner.log_startup()
        finally:
            root.removeHandler(cap)
        self.assertFalse(any("SECRET-TOKEN-123" in line for line in cap.lines), cap.lines)


if __name__ == "__main__":
    unittest.main()
