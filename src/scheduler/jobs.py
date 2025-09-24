import logging

from src.app import app
from src.scheduler.booking_sitemap import export_sitemap_ndjson


log = logging.getLogger(__name__)


def crawl_popular() -> None:
  """Placeholder scheduled job."""
  print("[scheduler] cron triggered: crawl_popular")
  log.info("[scheduler] cron triggered: crawl_popular")


def ingest_booking_sitemaps() -> None:
  """Fetch new Booking.com sitemap data and upsert hotel listings."""
  try:
    with app.app_context():
      export_sitemap_ndjson()
  except Exception:
    log.exception("booking sitemap ingest failed")
    raise
  else:
    log.info("booking sitemap ingest completed")
