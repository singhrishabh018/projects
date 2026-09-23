import os

PARTNER_BASE_URL = os.environ.get("PARTNER_BASE_URL", "https://partner.example.test")
PARTNER_TOKEN = os.environ.get("PARTNER_TOKEN", "")
ELIGIBLE_BRANDS_CSV = os.environ.get("ELIGIBLE_BRANDS_CSV", "/data/exports/eligible_brands.csv")
CONSUMER_GROUP = "price-sync"
ADMIN_PORT = int(os.environ.get("ADMIN_PORT", "8081"))
