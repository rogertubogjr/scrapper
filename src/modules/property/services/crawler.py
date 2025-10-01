"""Crawl4AI-backed scraping helpers for property listings."""

import json
import re
import logging
import os
from typing import Any, Dict, List

from crawl4ai import (
  AsyncWebCrawler,
  BrowserConfig,
  CacheMode,
  CrawlerRunConfig,
  JsonXPathExtractionStrategy,
  MemoryAdaptiveDispatcher,
)

from .config import _get_bool, _get_str
log = logging.getLogger(__name__)


async def run_crawler(url: str) -> Dict[str, Any]:
  headless_mode = _get_bool("PLAYWRIGHT_HEADLESS", True)
  artifact_directory = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_directory, exist_ok=True)
  except Exception:
    pass

  proxy_server = _get_str("PLAYWRIGHT_PROXY_SERVER")
  proxy_username = _get_str("PLAYWRIGHT_PROXY_USERNAME")
  proxy_password = _get_str("PLAYWRIGHT_PROXY_PASSWORD")

  proxy_config = None
  is_proxy_enabled = _get_bool("PROXY_ENABLED", False)
  if is_proxy_enabled and proxy_server:
    proxy_config = {"server": proxy_server}
    if proxy_username:
      proxy_config["username"] = proxy_username
    if proxy_password:
      proxy_config["password"] = proxy_password

  browser_config = BrowserConfig(headless=headless_mode, proxy_config=proxy_config)
  property_cards_ready_script = """() => {
        const items = document.querySelectorAll('[data-testid=\"property-card\"]');
        return items.length > 3;
    }"""
  load_more_results_script = """
      const btn = Array.from(document.querySelectorAll("button span"))
      .find(el => el.textContent.trim() === "Load more results");
      console.log('Trii-------')
      btn?.click();
  """
  wait_until_no_load_more = """js:() => {
      const btn = Array.from(document.querySelectorAll("button span"))
      .find(el => el.textContent.trim() === "Load more results");

      if(btn) {
          return false
      } else {
          return true
      }
  }"""
  session_identifier = "hoter_properties"

  schema = {
    "name": "Hotels",
    "baseSelector": "//div[@data-testid='property-card']",
    "fields": [
      {
        "name": "title",
        "selector": ".//div[@data-testid='title']",
        "type": "text",
      },
      {
        "name": "link",
        "selector": ".//a[contains(@href,'/hotel/')][1]",
        "type": "attribute",
        "attribute": "href",
      },
      {
        "name": "location",
        "selector": ".//span[contains(text(),'km') or contains(text(),'from') or contains(text(),'Show on map')]/..",
        "type": "text",
      },
      {
        "name": "rating_reviews",
        "selector": ".//div[@data-testid='review-score' or .//span[contains(text(),'review')]]",
        "type": "text",
      },
      {
        "name": "room_info",
        "selector": ".//div[contains(., 'Room') or .//h4]",
        "type": "text",
      },
      {
        "name": "price",
        "selector": ".//span[@data-testid='price-and-discounted-price']",
        "type": "text",
      },
      {
        "name": "fees",
        "selector": ".//div[contains(., 'tax') or contains(., 'fee')]",
        "type": "text",
      },
    ],
  }

  initial_run_config = CrawlerRunConfig(
    extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True),
    wait_for=f"js:{property_cards_ready_script}",
    scan_full_page=True,
    exclude_all_images=True,
    session_id=session_identifier
  )

  async with AsyncWebCrawler(verbose=True, config=browser_config) as crawler:
    result = await crawler.arun(
      url=url,
      config=initial_run_config,
    )

    remaining_iterations = 10
    same_length_count = 0
    while True:
      remaining_iterations -= 1
      if remaining_iterations == 0:
        break

      pagination_config = CrawlerRunConfig(
          extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True),
          session_id=session_identifier,
          js_code=load_more_results_script,
          wait_for=wait_until_no_load_more,
          js_only=True,
          cache_mode=CacheMode.BYPASS,
          scan_full_page=True,
          exclude_all_images=True,
      )
      pagination_result = await crawler.arun(
          url=url,
          config=pagination_config
      )
      if not result.success:
        print('\n\n ERROR \n\n')
        break
      if pagination_result.success:

        if (pagination_result.extracted_content and len(json.loads(pagination_result.extracted_content)) > 100):
          break

        pagination_length = len(json.loads(pagination_result.extracted_content))
        current_length = len(json.loads(result.extracted_content))
        if pagination_length == current_length:
          print(f'\n\n SAME LENGTH RESULT [{same_length_count}]\n\n')
          same_length_count += 1
          if same_length_count == 3:
            break
        result = pagination_result

    if not result.success:
      log.warning("Crawl failed: %s", result.error_message)
      return {
        "count": 0,
        "items": [],
        "source": "crawl4ai",
        "headless": headless_mode,
        "error": result.error_message or "crawl_failed",
      }

    parsed_items: List[Dict[str, str]] = []
    try:
      extracted_payload = result.extracted_content or "[]"
      parsed_payload = json.loads(extracted_payload)
      if isinstance(parsed_payload, list):
        for entry in parsed_payload:
          if not isinstance(entry, dict):
            continue
          parsed_item: Dict[str, str] = {}
          title = entry.get("title")
          link = entry.get("link")
          location = entry.get("location")
          rating = entry.get("rating_reviews")
          room_info = entry.get("room_info")
          price = entry.get("price")
          fees = entry.get("fees")

          if isinstance(title, str) and title.strip():
            parsed_item["title"] = title.strip()
          if isinstance(link, str) and link.strip():
            normalized_link = link.strip()
            if normalized_link.startswith("/"):
              normalized_link = "https://www.booking.com" + normalized_link
            parsed_item["link"] = normalized_link
          if isinstance(location, str) and location.strip():
            parsed_item["location"] = location.strip().replace('Show on map','')
          if isinstance(rating, str) and rating.strip():
            parsed_item["rating_reviews"] = rating.strip()
          if isinstance(room_info, str) and room_info.strip():
            parsed_item["room_info"] = room_info.strip()
          if isinstance(price, str) and price.strip():
            parsed_item["price"] = price.strip()
          if isinstance(fees, str) and fees.strip():
            parsed_item["fees"] = fees.strip()
          if parsed_item:
            parsed_items.append(parsed_item)
    except Exception as exc:
      log.debug("Failed parsing extracted content: %s", exc)

    return {
      "count": len(parsed_items),
      "items": parsed_items,
      "source": "crawl4ai",
      "headless": headless_mode,
    }


async def crawl_per_page_currently(urls):
  if not urls:
    return []

  headless = _get_bool("PLAYWRIGHT_HEADLESS", True)

  browser_cfg = BrowserConfig(headless=headless)
  wait_condition = """() => {
      const items = document.querySelectorAll('[data-testid="poi-block"]');
    return items.length > 0
  }"""

  schema = {
    "baseSelector": "//div[@id='hotelTmpl']",
    "fields": [
      {
        "name": "location",
        "selector": "//div[@data-testid='PropertyHeaderAddressDesktop-wrapper']//button/div",
        "type": "text",
      },
      {
        "name": "facilities",
        "selector": "//div[@data-testid='property-most-popular-facilities-wrapper']//ul//li",
        "type": "list",
        "fields": [
          {
            "name":"facility",
            "selector":"//div",
            "type":"text",
          },
        ]
      },
      {
        "name": "price_info",
        "selector": "//table[@id='hprt-table']//tr",
        "type": "nested_list",
        "fields": [
              {
                "name":"room_type",
                "selector":".//th[1]",
                "type":"text",
              },
              {
                "name":"occupancy",
                "selector":".//td[contains(@class, 'hprt-table-cell-occupancy')] | .//td[1]",
                "type":"text",
              },
              {
                "name":"payable",
                "selector":".//td[contains(@class, 'hprt-table-cell-price')]//span | .//td[2]//span",
                "type":"text",
              },
              {
                "name":"conditions",
                "selector":".//td[contains(@class, 'hprt-table-cell-conditions')]//ul//li",
                "type":"list",
                "fields": [
                            {
                                "name": "name",
                                "selector": ".//div",
                                "type": "text"
                            },
                        ]
              },
          ]
      },
      {
        "name": "area_info",
        "selector": "//div[@data-testid='location-block-container']//div[@data-testid='poi-block']",
        "type": "nested_list",
        "fields": [
          {
            "name":"category",
            "selector":"./div",
            "type":"text",
          },
          {
            "name":"areas",
            "selector":"./ul//li",
            "type":"list",
            "fields": [
                      {
                          "name": "area",
                          "selector":".//div",
                          "type": "text"
                      },
                  ]
          },
        ]
      }
    ]
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

    page_data = []

    for result in results:
      if not result.success or not result.extracted_content:
        log.debug("crawl failed for %s: %s", result.url, result.error_message)
        continue

      raw = result.extracted_content or "[]"
      data = json.loads(raw)

      if not isinstance(data, list):
        continue

      for item in data:
        info_prices = []
        counter = -1
        location = ''
        if 'location' in item:
          location = item['location'].split('After booking')[0].split('Excellent location')[0]

        if 'price_info' in item:
          for price_info in item['price_info']:
            if 'room_type' in price_info and 'occupancy' in price_info:
              if 'room_type' in price_info:
                info_price = dict(
                  room_type = '',
                  room_category = []
                )
                info_price['room_type'] = re.sub(r'\n+| {2,}', lambda m: '\n' if '\n' in m.group() else ' ', price_info['room_type'])
                info_prices.append(info_price)
                counter += 1

            if 'occupancy' in price_info:
              info_prices[counter]['room_category'].append(dict(
                occupancy = re.sub(r'\n+| {2,}', lambda m: '\n' if '\n' in m.group() else ' ', price_info['occupancy']),
                payable = (re.sub(r'\n+| {2,}', lambda m: '\n' if '\n' in m.group() else ' ', price_info['payable'])).replace('\xa0', ' '),
                conditions = price_info['conditions']
              ))

        page_data.append(dict(
          location = location,
          facilities = item['facilities'],
          info_prices = info_prices,
          area_info = item['area_info'],
          url = result.url
        ))

    return page_data
