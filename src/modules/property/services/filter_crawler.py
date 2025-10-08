import json
from typing import Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, JsonXPathExtractionStrategy

from .config import _get_bool, _get_str, _get_float, _get_int

async def filter_crawler(url, session_id):
  checkbox_filter_code: Dict[str, str] = {}

  proxy_config = None
  proxy_server = _get_str("PLAYWRIGHT_PROXY_SERVER")
  proxy_username = _get_str("PLAYWRIGHT_PROXY_USERNAME")
  proxy_password = _get_str("PLAYWRIGHT_PROXY_PASSWORD")

  is_proxy_enabled = _get_bool("PROXY_ENABLED", False)
  if is_proxy_enabled and proxy_server:
    proxy_config = {"server": proxy_server}
    if proxy_username:
      proxy_config["username"] = proxy_username
    if proxy_password:
      proxy_config["password"] = proxy_password
  headless_mode = _get_bool("PLAYWRIGHT_HEADLESS", True)

  browser_config = BrowserConfig(headless=headless_mode, proxy_config=proxy_config)

  wait_condition = """() => {
    const items = document.querySelectorAll('[data-testid="filters-group-label-content"]');
    return items.length > 5
  }"""

  schema = {
    "baseSelector": "//div[@data-testid='filters-sidebar']",
    "fields": [
      {
        "name": "all_filters",
        "selector": ".//div[@data-testid='filters-group']",
        "type": "nested_list",
        "fields": [
          {
            "name": "name",
            "selector": "./fieldset//legend",
            "type": "text"
          },
          {
            "name": "filter-group",
            "selector": "./fieldset//div",
            "type": "list",
            "fields": [
              {
                "name": "value",
                "selector": ".//input",
                "type": "attribute",
                "attribute": "value"
              },
              {
                "name": "ariaLabel",
                "selector": ".//input",
                "type": "attribute",
                "attribute": "aria-label"
              },
            ]
          }
        ]
      }
    ]
  }

  config = CrawlerRunConfig(
    extraction_strategy=JsonXPathExtractionStrategy(schema),
    wait_for=f"js:{wait_condition}",
    scan_full_page= True,
    exclude_all_images=True,
    session_id=session_id
  )

  async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
      url=url,
      config=config,
    )

    if result.success:
      raw = result.extracted_content or "[]"
      data = json.loads(raw)

      loop_limit = 3
      scrape_again = True
      no_scrape_data = 0

      if len(data) and 'all_filters' in data[0]:
        no_scrape_data = len(data[0]['all_filters'])

      if no_scrape_data < 20:
        while scrape_again:
          print(f' \n\n\n while loop \n\n\n')
          loop_limit -= 1
          if loop_limit == 0:
            break

          config_next = CrawlerRunConfig(
              extraction_strategy=JsonXPathExtractionStrategy(schema),
              session_id=session_id,
              wait_for=wait_condition,
              js_only=True,       # We're continuing from the open tab
              cache_mode=CacheMode.BYPASS,
              scan_full_page= True,
              exclude_all_images=True,
          )
          result2 = await crawler.arun(
              url=url,
              config=config_next
          )

          if result2.success:
            data_extracted2 = json.loads(result2.extracted_content)

            if 'all_filters' in data_extracted2[0]:
              no_scrape_data2 = len(data_extracted2[0]['all_filters'])

              if no_scrape_data > 5 and no_scrape_data == no_scrape_data2:
                break

              no_scrape_data = no_scrape_data2

              print('+++', no_scrape_data)

          else:
            print('\nNO DATA\n')

      for i in data[0]['all_filters']:
        if 'Your budget (per night)' not in i['name']:
          print('\n', i['name'])
          for x in i['filter-group']:
            value = None
            ariaLabel = None
            if 'value' in x and len(x['value']):
              value = x['value']
            if 'ariaLabel' in x and len(x['ariaLabel']):
              ariaLabel = x['ariaLabel']
            if value and ariaLabel:
              print(f"\t{value} | {ariaLabel}")
              filter_key = ariaLabel.split(":")[0]
              filter_code = value.replace("=", "%3D")

              if filter_key not in checkbox_filter_code:
                checkbox_filter_code[filter_key] = filter_code

    return checkbox_filter_code