import asyncio, os, json, logging
from typing import Any, Dict, List

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    JsonXPathExtractionStrategy,
    LLMConfig,
    LLMExtractionStrategy,
    MemoryAdaptiveDispatcher,
)
from flask import current_app


log = logging.getLogger(__name__)

from typing import List, Dict
from pydantic import BaseModel, Field, HttpUrl

class SitemapUrl(BaseModel):
  sitemap_urls: str = Field(..., description="Fully qualified Booking sitemap XML URL (e.g., https://…/..index.xml).")



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


async def crawl_robots_txt():
  # 1. Define the LLM extraction strategy
  llm_strategy = LLMExtractionStrategy(
      llm_config = LLMConfig(provider="openai/gpt-5-mini", api_token=os.getenv('OPENAI_API_KEY')),
      schema=SitemapUrl.model_json_schema(), # Or use model_json_schema()
      extraction_type="schema",
      instruction="""
        Extract only the fully-qualified Booking sitemap XML URLs present in the provided text
        (for example, https://www.booking.com/sitemaps/...-index.xml).
        The content is delivered in multiple chunks; treat each chunk independently and
        do not follow, expand, or fetch any referenced URLs—simply collect the absolute
        URLs that already appear in the text.
      """,
      chunk_token_threshold=3000,
      overlap_rate=0.2,
      apply_chunking=True,
      input_format="markdown",   # or "html", "fit_markdown"
      extra_args={"temperature": 1}
  )

  # 2. Build the crawler config
  crawl_config = CrawlerRunConfig(
      extraction_strategy=llm_strategy,
      cache_mode=CacheMode.BYPASS,
      screenshot=True,
      pdf=True,
      scan_full_page=True,  # Tells the crawler to try scrolling the entire page
      scroll_delay=0.5,     # Delay (seconds) between scroll steps
      # wait_for_images=True,
  )

  # 3. Create a browser config if needed
  browser_cfg = BrowserConfig(headless=True)

  async with AsyncWebCrawler(config=browser_cfg) as crawler:
      # 4. Let's say we want to crawl a single page
      result = await crawler.arun(
          url="https://www.booking.com/robots.txt",
          config=crawl_config
      )
      print(result.extracted_content)
