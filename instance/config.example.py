"""
Example Flask instance configuration.

Usage
- Copy this file to `instance/config.py` (same directory).
- Set real values via environment variables or in `instance/config.py` locally.
- Do NOT commit secrets; `.gitignore` keeps `instance/config.py` untracked.
"""

import os
from dotenv import load_dotenv


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except ValueError:
        return default


# Load environment variables from a .env file if present
load_dotenv()

# Core app settings
DEBUG = _get_bool("DEBUG", True)

# Auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
TOKEN = os.getenv("TOKEN", "CHANGE_ME_TOKEN")

# Playwright settings
PLAYWRIGHT_HEADLESS = _get_bool("PLAYWRIGHT_HEADLESS", True)
PLAYWRIGHT_STEALTH = _get_bool("PLAYWRIGHT_STEALTH", True)
PLAYWRIGHT_DEBUG_ARTIFACTS = _get_bool("PLAYWRIGHT_DEBUG_ARTIFACTS", False)
PLAYWRIGHT_DEBUG_PRINT = _get_bool("PLAYWRIGHT_DEBUG_PRINT", False)
PLAYWRIGHT_DEBUG_PRINT_MAX = _get_int("PLAYWRIGHT_DEBUG_PRINT_MAX", 10000)
PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
]
PLAYWRIGHT_ARTIFACT_DIR = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))

# Scheduler / ingest defaults
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CRON_POPULAR = os.getenv("CRON_POPULAR", "0 * * * *")
CRON_BOOKING_SITEMAP = os.getenv("CRON_BOOKING_SITEMAP", "0 * * * *")

SITEMAP_DIR = os.getenv("SITEMAP_DIR", "/app/sitemap_data")
SITEMAP_WORKER_THREADS = _get_int("SITEMAP_WORKER_THREADS", 4)
PARALLEL_URL_TO_SCRAPE = _get_int("PARALLEL_URL_TO_SCRAPE", 10)

SQLALCHEMY_DATABASE_URI = "postgresql://postgres:password@db/db"
