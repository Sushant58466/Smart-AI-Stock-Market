import os
from dotenv import load_dotenv
load_dotenv()

APP_NAME = "Smart Stock AI"
DEFAULT_DATA_PROVIDER = os.getenv("DEFAULT_DATA_PROVIDER", "Yahoo Finance")
ENABLE_PROVIDER_FAILOVER = os.getenv("ENABLE_PROVIDER_FAILOVER", "true").lower() == "true"
CACHE_TTL_SECONDS = max(0, int(os.getenv("CACHE_TTL_SECONDS", "60")))
API_KEYS = {
    "Twelve Data": os.getenv("TWELVE_DATA_API_KEY", "").strip(),
    "Alpha Vantage": os.getenv("ALPHA_VANTAGE_API_KEY", "").strip(),
    "Finnhub": os.getenv("FINNHUB_API_KEY", "").strip(),
}
PROVIDERS = ["Yahoo Finance", "Twelve Data", "Alpha Vantage", "Finnhub"]
