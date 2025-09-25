"""Shared helpers for Booking sitemap workflows."""

from __future__ import annotations

import os
from typing import Tuple


def get_env_int(name: str, default: int) -> int:
    """Read an integer environment variable with a safe fallback."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def get_sitemap_base_dir() -> str:
    return os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "/app/sitemap_data"))


def resolve_dirs() -> Tuple[str, str, str]:
    base_dir = get_sitemap_base_dir()
    xml_dir = os.path.join(base_dir, "xml")
    ndjson_dir = os.path.join(base_dir, "ndjson")
    os.makedirs(xml_dir, exist_ok=True)
    os.makedirs(ndjson_dir, exist_ok=True)
    return base_dir, xml_dir, ndjson_dir

