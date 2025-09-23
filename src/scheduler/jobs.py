import logging, requests, re

log = logging.getLogger(__name__)


def crawl_popular() -> None:
  """Placeholder scheduled job.

  For now, only prints/logs when the cron trigger fires. Replace this with
  real logic later (e.g., calling your use-cases).
  """
  print("[scheduler] cron triggered: crawl_popular")
  log.info("[scheduler] cron triggered: crawl_popular")


