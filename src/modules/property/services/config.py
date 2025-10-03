"""Config helpers shared across property module services."""

import os
from typing import Optional

from flask import current_app


def _get_bool(name: str, default: bool) -> bool:
  cfg = current_app.config if current_app else {}
  v = cfg.get(name)
  if v is None:
    v = os.getenv(name)
  if v is None:
    return default
  return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _get_str(name: str, default: Optional[str] = None) -> Optional[str]:
  """Return a config/environment string with fallback whitespace stripping."""
  cfg = current_app.config if current_app else {}
  v = cfg.get(name)
  if v is None:
    v = os.getenv(name)
  if v is None:
    return default
  v = str(v).strip()
  return v or default


def _get_int(name: str, default: int) -> int:
  value = _get_str(name)
  if value is None:
    return default
  try:
    return int(value)
  except (TypeError, ValueError):
    return default


def _get_float(name: str, default: float) -> float:
  value = _get_str(name)
  if value is None:
    return default
  try:
    return float(value)
  except (TypeError, ValueError):
    return default
