import asyncio
import json
import logging
from typing import Any, Dict, List

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    JsonXPathExtractionStrategy,
    MemoryAdaptiveDispatcher,
)
from flask import current_app


log = logging.getLogger(__name__)


def _get_bool(name: str, default: bool) -> bool:
    cfg = current_app.config if current_app else {}
    value = cfg.get(name)
    if value is None:
        import os

        value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def run_async(coro):
    """Run an async coroutine from synchronous code."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def run_crawler(urls: List[str]) -> List[Dict[str, Any]]:
    if not urls:
        return []

    headless = _get_bool("PLAYWRIGHT_HEADLESS", True)

    browser_cfg = BrowserConfig(headless=headless)
    wait_condition = """() => {
        const items = document.querySelectorAll('[data-testid=\"PropertyHeaderAddressDesktop-wrapper\"] button div');
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
    )
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        max_session_permit=10,
    )

    async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher,
        )

    url_and_locations: List[Dict[str, Any]] = []
    for result in results:
        if not result.success or not result.extracted_content:
            log.debug("crawl failed for %s: %s", result.url, result.error_message)
            continue

        raw = result.extracted_content or "[]"
        data = json.loads(raw)
        if not isinstance(data, list):
            continue

        for item in data:
            if not isinstance(item, dict):
                continue
            location = item.get("location")
            if not location:
                continue
            location = location.split('After booking')[0].split('Excellent location')[0]
            url_and_locations.append({"location": location, "url": result.url})

    return url_and_locations

