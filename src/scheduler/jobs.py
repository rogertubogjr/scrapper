import logging

from src.app import app
from src.scheduler.booking_sitemap import (
  ingest_booking_sitemaps_from_ndjson,
  materialize_booking_sitemaps,
)


log = logging.getLogger(__name__)


def crawl_popular() -> None:
  """Placeholder scheduled job."""
  print("[scheduler] cron triggered: crawl_popular")
  log.info("[scheduler] cron triggered: crawl_popular")


def materialize_booking_sitemaps_job() -> None:
  """Download Booking.com sitemap XML files and convert to NDJSON."""
  try:
    with app.app_context():
      materialize_booking_sitemaps()
  except Exception:
    log.exception("booking sitemap materialization failed")
    raise
  else:
    log.info("booking sitemap materialization completed")


def ingest_booking_sitemaps() -> None:
  """Fetch new Booking.com sitemap data and upsert hotel listings."""
  try:
    with app.app_context():
      ingest_booking_sitemaps_from_ndjson()
  except Exception:
    log.exception("booking sitemap ingest failed")
    raise
  else:
    log.info("booking sitemap ingest completed")
