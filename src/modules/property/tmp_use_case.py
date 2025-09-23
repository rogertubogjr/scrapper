import os, json, re, asyncio, logging, time, gzip, requests
from base64 import b64decode
from typing import Any, Dict, List, Iterator, Optional
from crawl4ai import (
  AsyncWebCrawler,
  BrowserConfig,
  CrawlerRunConfig,
  JsonXPathExtractionStrategy,
)
from agents import Runner
from datetime import date, timedelta
import xml.etree.ElementTree as ET

from flask import current_app
from playwright.async_api import async_playwright
from src.agent_helpers.destination_extractor import ah_destination_extractor
from src.agent_helpers.booking_search_url_agent import booking_search_url_agent
from src.handler.error_handler import InvalidDataError, NotFoundError, UnexpectedError

log = logging.getLogger(__name__)


def run_async(coro):
  """Run async coroutine from sync context safely."""
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  try:
    return loop.run_until_complete(coro)
  finally:
    loop.close()


def _get_bool(name: str, default: bool) -> bool:
  cfg = current_app.config if current_app else {}
  v = cfg.get(name)
  if v is None:
    v = os.getenv(name)
  if v is None:
    return default
  return str(v).strip().lower() in {"1", "true", "yes", "on"}

async def run_crawler(url) -> Dict[str, Any]:
  headless = _get_bool("PLAYWRIGHT_HEADLESS", True)
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass

  browser_cfg = BrowserConfig(headless=headless)
  wait_condition = """() => {
        const items = document.querySelectorAll('[data-testid=\"PropertyHeaderAddressDesktop-wrapper\"]');
        return items.length > 0;
    }"""

  schema = {
    "name": "Hotels",
    "baseSelector": "//div[@data-testid='PropertyHeaderAddressDesktop-wrapper']",
    "fields": [
      {
        "name": "location",
        "selector": "button div",
        "type": "text",
      }
    ],
  }

  config = CrawlerRunConfig(
    extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True),
    wait_for=f"js:{wait_condition}",
    scan_full_page=True,
    scroll_delay=1.2,
    screenshot=True,
    pdf=True,
  )

  async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
    result = await crawler.arun(
      url=url,
      config=config,
    )
    if result.screenshot:
      print(f"[OK] Screenshot captured, size: {len(result.screenshot)} bytes")
      with open("wikipedia_screenshot.png", "wb") as f:
        f.write(b64decode(result.screenshot))
    else:
      print("[WARN] Screenshot data is None.")
    if result.pdf:
      print(f"[OK] PDF captured, size: {len(result.pdf)} bytes")
      with open("wikipedia_page.pdf", "wb") as f:
        f.write(result.pdf)

    if not result.success:
      log.warning("Crawl failed: %s", result.error_message)
      return {
        "count": 0,
        "items": [],
        "source": "crawl4ai",
        "headless": headless,
        "error": result.error_message or "crawl_failed",
      }

    items: List[Dict[str, str]] = []
    print(result.extracted_content)
    try:
      raw = result.extracted_content or "[]"
      data = json.loads(raw)
      if isinstance(data, list):
        for x in data:
          if not isinstance(x, dict):
            continue
          itm: Dict[str, str] = {}
          location = x.get("location")

          if isinstance(location, str) and location.strip():
            itm["location"] = location.strip()
          if itm:
            items.append(itm)
    except Exception as e:
      log.debug("Failed parsing extracted content: %s", e)

    return {
      "count": len(items),
      "items": items,
      "source": "crawl4ai",
      "headless": headless,
    }

def get_location():
  crawl = run_async(run_crawler('https://www.booking.com/hotel/ad/abbasuitehotelandorra.html'))
  print(crawl,'-----------')