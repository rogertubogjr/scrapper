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


async def run_agent_action(input_data, agent, session=None, return_final_output=False):
  result = await Runner.run(
    agent,
    input_data,
    session=session,
  )
  if return_final_output:
    return result.final_output
  try:
    action = re.sub(r"```(?:json)?|```", "", result.final_output).strip()
    return json.loads(action)
  except Exception as e:
    print("Invalid JSON:", action, e)
    raise ValueError("Error occur on running agent")


async def run_crawler(url) -> Dict[str, Any]:
  headless = _get_bool("PLAYWRIGHT_HEADLESS", True)
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass

  proxy_server = _get_str("PLAYWRIGHT_PROXY_SERVER")
  proxy_username = _get_str("PLAYWRIGHT_PROXY_USERNAME")
  proxy_password = _get_str("PLAYWRIGHT_PROXY_PASSWORD")

  proxy_cfg = None
  if proxy_server:
    server = proxy_server.strip()
    if server and "://" not in server:
      server = f"http://{server}"

    proxy_cfg = {"server": server}
    if proxy_username:
      proxy_cfg["username"] = proxy_username
    if proxy_password:
      proxy_cfg["password"] = proxy_password

    if proxy_username and not proxy_password:
      log.warning("Proxy username provided without password; continuing without auth")
    if proxy_password and not proxy_username:
      log.warning("Proxy password provided without username; continuing without auth")

  browser_cfg = BrowserConfig(headless=headless, proxy_config=proxy_cfg)
  if proxy_cfg:
    try:
      log.debug("run_crawler routing through proxy %s", proxy_cfg.get("server", ""))
    except Exception:
      log.debug("run_crawler routing through proxy")
  wait_condition = """() => {
        const items = document.querySelectorAll('[data-testid=\"property-card\"]');
        return items.length > 5;
    }"""

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

  config = CrawlerRunConfig(
    extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True),
    wait_for=f"js:{wait_condition}",
    scan_full_page=True,
    scroll_delay=1.2,
  )

  async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
    result = await crawler.arun(
      url=url,
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

    items: List[Dict[str, str]] = []
    try:
      raw = result.extracted_content or "[]"
      data = json.loads(raw)
      if isinstance(data, list):
        for x in data:
          if not isinstance(x, dict):
            continue
          itm: Dict[str, str] = {}
          title = x.get("title")
          link = x.get("link")
          location = x.get("location")
          rating = x.get("rating_reviews")
          room_info = x.get("room_info")
          price = x.get("price")
          fees = x.get("fees")

          if isinstance(title, str) and title.strip():
            itm["title"] = title.strip()
          if isinstance(link, str) and link.strip():
            l = link.strip()
            if l.startswith("/"):
              l = "https://www.booking.com" + l
            itm["link"] = l
          if isinstance(location, str) and location.strip():
            itm["location"] = location.strip()
          if isinstance(rating, str) and rating.strip():
            itm["rating_reviews"] = rating.strip()
          if isinstance(room_info, str) and room_info.strip():
            itm["room_info"] = room_info.strip()
          if isinstance(price, str) and price.strip():
            itm["price"] = price.strip()
          if isinstance(fees, str) and fees.strip():
            itm["fees"] = fees.strip()

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


async def run_playwright(url) -> Dict[str, Any]:
  """Scrape availability links using raw Playwright.

  - Keeps the Booking URL static (no env keys for URL).
  - Respects PLAYWRIGHT_HEADLESS and PLAYWRIGHT_ARTIFACT_DIR for runtime behavior.
  - Returns the same shape as run_crawler for consistency.
  """
  headless = _get_bool("PLAYWRIGHT_HEADLESS", True)
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass

  items: List[Dict[str, str]] = []

  proxy_server = _get_str("PLAYWRIGHT_PROXY_SERVER")
  proxy_username = _get_str("PLAYWRIGHT_PROXY_USERNAME")
  proxy_password = _get_str("PLAYWRIGHT_PROXY_PASSWORD")

  proxy_settings = None
  if proxy_server:
    proxy_settings = {"server": proxy_server}
    if proxy_username:
      proxy_settings["username"] = proxy_username
    if proxy_password:
      proxy_settings["password"] = proxy_password

  async with async_playwright() as pw:
    browser = await pw.chromium.launch(
      headless=headless,
      args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
      ],
      proxy=proxy_settings,
    )
    context = await browser.new_context(
      user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.5845.110 Safari/537.36"
      ),
      viewport={"width": 1366, "height": 768},
      locale="en-US",
      extra_http_headers={
        "Accept-Language": "en-US,en;q=0.9",
      },
    )

    await context.add_init_script(
      "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )

    page = await context.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    try:
      await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
      pass

    results = await page.evaluate("""() => {
            return Array.from(
            document.querySelectorAll('input[type=\"checkbox\"]')
            )
            .filter(el => {
            const aria = el.getAttribute('aria-label');
            return el.name && el.value && aria && aria.trim() !== '';
            })
            .map(el => ({
            name: el.name,
            value: el.value,
            ariaLabel: el.getAttribute('aria-label').trim()
            }));
        }""")

    checkbox_filter_code = ""

    for i in results:
      filter = i["ariaLabel"].split(":")[0]
      code = i["value"].replace("=", "%3D")
      checkbox_filter_code += f"• {filter} → {code}\n"

    await context.close()
    await browser.close()

    return checkbox_filter_code

  return {
    "count": len(items),
    "items": items,
    "source": "playwright",
    "headless": headless,
  }


def get_properties(prompt: str) -> Dict[str, Any]:
  """Extract destination from a free‑form prompt using the agent.

  - Validates input and enforces a timeout to avoid hanging requests.
  - Maps errors to typed HTTP-friendly exceptions.
  - Returns a structured dict: { destination, source, duration_ms }.
  """
  if not isinstance(prompt, str):
    raise InvalidDataError("Field 'prompt' must be a string.")
  prompt = prompt.strip()
  if not prompt:
    raise InvalidDataError("Field 'prompt' is required and must be non-empty.")

  log_prompt = prompt if len(prompt) <= 256 else (prompt[:256] + "…")

  started = time.monotonic()
  try:
    destination_data = run_async(
      asyncio.wait_for(
        run_agent_action(prompt, ah_destination_extractor, None, False),
        timeout=30,
      )
    )
  except asyncio.TimeoutError:
    duration_ms = int((time.monotonic() - started) * 1000)
    log.warning(
      "destination extraction timed out; duration_ms=%d prompt='%s'",
      duration_ms,
      log_prompt,
    )
    raise UnexpectedError("Destination extraction timed out.")
  except InvalidDataError:
    raise
  except Exception as e:
    duration_ms = int((time.monotonic() - started) * 1000)
    log.exception(
      "destination extraction failed; duration_ms=%d error=%s",
      duration_ms,
      e,
    )
    raise UnexpectedError("Destination extraction failed.")

  destination = None
  if isinstance(destination_data, dict):
    destination = destination_data.get("destination")

  if not isinstance(destination, str) or not destination.strip():
    raise NotFoundError("No destination extracted from the prompt.")

  destination = destination.strip()
  duration_ms = int((time.monotonic() - started) * 1000)
  log.debug("destination extracted; duration_ms=%d dest='%s'", duration_ms, destination)

  date_f_str = date.today().strftime("%Y-%m-%d")
  date_t_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
  initial_url = (
    f"https://www.booking.com/searchresults.html?ss={destination}"
    f"&search_selected=true&checkin={date_f_str}&checkout={date_t_str}"
    f"&group_adults=2&no_rooms=1&group_children=0"
  )

  def _parse_checkbox_filters(bulleted: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not isinstance(bulleted, str):
      return mapping
    for line in bulleted.splitlines():
      line = line.strip()
      if not line:
        continue
      sep = "→" if "→" in line else ("->" if "->" in line else None)
      if not sep:
        continue
      left, right = line.split(sep, 1)
      name = left.replace("•", "").strip()
      code = right.strip()
      if name and code:
        mapping[name] = code
    return mapping

  raw_filters = run_async(run_playwright(initial_url))
  filters_map = _parse_checkbox_filters(raw_filters)
  filters_json = json.dumps(filters_map, ensure_ascii=False)

  url_agent = booking_search_url_agent(filters_json)
  url_data = run_async(run_agent_action(prompt, url_agent, None, False))
  if not isinstance(url_data, dict) or "url" not in url_data or not url_data["url"]:
    raise UnexpectedError("Failed to generate a search URL.")

  final_url = url_data["url"]

  crawl = run_async(run_crawler(final_url))
  if not isinstance(crawl, dict):
    crawl = {
      "count": 0,
      "items": [],
      "source": "crawl4ai",
      "headless": _get_bool("PLAYWRIGHT_HEADLESS", True),
    }
  crawl["destination"] = destination
  crawl.pop("headless", None)
  crawl.pop("url", None)
  return crawl
