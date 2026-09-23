import os

PARTNER_BASE_URL = os.environ.get("PARTNER_BASE_URL", "https://partner.example.test")
PARTNER_TOKEN = os.environ.get("PARTNER_TOKEN", "")
PARTNER_TIMEOUT = 10  # seconds
PARTNER_MAX_RETRIES = 3

BROKER_URL = os.environ.get("BROKER_URL", "broker://localhost:9092")
CONSUMER_GROUP = "stock-sync"
SENT_LOG_PATH = os.environ.get("SENT_LOG_PATH", "/var/lib/stock-sync/sent.db")
BRANDS_CSV = os.environ.get("BRANDS_CSV", "/data/exports/brands.csv")
