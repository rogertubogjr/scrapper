import asyncio
import logging
import os, json
from base64 import b64decode
from typing import Any, Dict, List
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    JsonXPathExtractionStrategy,
)

from flask import current_app

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


async def run_crawler() -> Dict[str, Any]:
    headless = _get_bool("PLAYWRIGHT_HEADLESS", True)
    # Save artifacts under repo-local directory by default; override via env
    artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except Exception:
        pass

    browser_cfg = BrowserConfig(headless=headless)
    wait_condition = """() => {
        const items = document.querySelectorAll('[data-testid="property-card"]');
        return items.length > 5;
    }"""

    schema = {
      "name": "Hotels",
      "baseSelector": "//div[@data-testid='property-card']",
      "fields": [
            {
              "name":"availability_link",
              "selector":".//div[@data-testid='availability-cta']/a",
              "type":"attribute",
              "attribute":"href"
            }
        ]
    }

    config = CrawlerRunConfig(
        extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True),
        wait_for=f"js:{wait_condition}",
        scan_full_page= True,
        scroll_delay=2,
        screenshot=True,
        pdf=True,
    )

    async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
        result = await crawler.arun(
            # NOTE: Keeping URL static as requested
            url='https://www.booking.com/searchresults.html?ss=Cebu&search_selected=true&checkin=2025-11-15&checkout=2025-11-20&group_adults=2&no_rooms=1&group_children=2&nflt=price%3DEUR-150-300-1%3Broomfacility%3D11',
            config=config,
        )

        if not result.success:
            log.warning("Crawl failed: %s", result.error_message)
            return {
                "count": 0,
                "items": [],
                "source": "crawl4ai",
                "headless": headless,
                "error": result.error_message or "crawl_failed",
            }

        # Save artifacts when available
        if result.screenshot:
            try:
                out_path = os.path.join(artifact_dir, "booking_screenshot.png")
                with open(out_path, "wb") as f:
                    f.write(b64decode(result.screenshot))
                log.debug("Saved screenshot: %s", out_path)
            except Exception as e:
                log.debug("Failed saving screenshot: %s", e)
        if result.pdf:
            try:
                out_pdf = os.path.join(artifact_dir, "booking_page.pdf")
                with open(out_pdf, "wb") as f:
                    f.write(result.pdf)
                log.debug("Saved PDF: %s", out_pdf)
            except Exception as e:
                log.debug("Failed saving PDF: %s", e)

        # Extract structured items from JSON string
        items: List[Dict[str, str]] = []
        try:
            data = json.loads(result.extracted_content) if result.extracted_content else []
            if isinstance(data, list):
                for x in data:
                    if isinstance(x, dict) and x.get("availability_link"):
                        items.append({"availability_link": x.get("availability_link")})
        except Exception as e:
            log.debug("Failed parsing extracted content: %s", e)

        return {
            "count": len(items),
            "items": items,
            "source": "crawl4ai",
            "headless": headless,
        }

def get_properties() -> Dict[str, Any]:
    """Synchronous entrypoint returning structured results."""
    return run_async(run_crawler())
