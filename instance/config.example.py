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


# Load environment variables from a .env file if present
load_dotenv()

# Core app settings
DEBUG = _get_bool("DEBUG", True)

# Auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
TOKEN = os.getenv("TOKEN", "CHANGE_ME_TOKEN")

# Playwright settings
PLAYWRIGHT_HEADLESS = _get_bool("PLAYWRIGHT_HEADLESS", True)
PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
]

SQLALCHEMY_DATABASE_URI = "postgresql://postgres:password@db/db"
