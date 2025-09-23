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

  browser_cfg = BrowserConfig(headless=headless)
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

  async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=headless, args=[
      "--disable-blink-features=AutomationControlled",
      "--no-sandbox",
      "--disable-setuid-sandbox",
    ])
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

def test() -> List[Dict[str, str]]:
  """Fetch hotel sitemap index and list child .xml.gz entries.

  Resolves issues with .xml.gz and XML namespaces.
  Returns a list of {loc, lastmod}.
  """
  robots_url = "https://www.booking.com/robots.txt"
  headers = {
    "User-Agent": (
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36"
    )
  }

  try:
    resp = requests.get(robots_url, timeout=15, headers=headers)
    resp.raise_for_status()
  except requests.RequestException as e:
    log.warning("robots fetch failed: %s", e)
    return []

  sitemap_urls = re.findall(r"^Sitemap:\s*(\S+)$", resp.text, re.MULTILINE | re.IGNORECASE)

  # Prefer NL hotel sitemap index if present
  index_url = None
  for url in sitemap_urls:
    if "sitembk-hotel-nl" in url and "index" in url:
      index_url = url
      break
  if not index_url:
    for url in sitemap_urls:
      if "sitembk-hotel" in url and "index" in url:
        index_url = url
        break
  if not index_url:
    return []

  print(index_url)

  r2 = requests.get(index_url, timeout=20, headers=headers)
  r2.raise_for_status()
  content = r2.content
  # if index_url.endswith(".gz") or "gzip" in r2.headers.get("Content-Type", "").lower():
  #   try:
  #     content = gzip.decompress(content)
  #   except OSError:
  #     pass

  try:
    root = ET.fromstring(content)
  except ET.ParseError as e:
    log.warning("sitemap XML parse failed: %s", e)
    return []

  ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
  out: List[Dict[str, str]] = []
  for node in root.findall("sm:sitemap", ns):
    loc_el = node.find("sm:loc", ns)
    lastmod_el = node.find("sm:lastmod", ns)
    if 'en-us' not in loc_el.text.strip() or loc_el is None or not (loc_el.text or "").strip():
      continue
    out.append({
      "loc": loc_el.text.strip(),
      "lastmod": (lastmod_el.text.strip() if (lastmod_el is not None and lastmod_el.text) else None),
    })

  # print(out)
  for i in out:
    print(i)

  url_xml_gz = 'https://www.booking.com/sitembk-hotel-en-us.0000.xml.gz'
  # Download the gzip sitemap and save decompressed XML to /tmp
  try:
    r3 = requests.get(url_xml_gz, timeout=30, headers=headers)
    r3.raise_for_status()
    gz_bytes = r3.content
  except requests.RequestException as e:
    log.warning("gz sitemap fetch failed: %s", e)
    return out

  # Decompress .gz → XML bytes (fallback if server sends plain XML)
  try:
    xml_bytes = gzip.decompress(gz_bytes)
  except OSError:
    xml_bytes = gz_bytes

  # Persist for inspection under artifacts directory
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass
  out_path = os.path.join(artifact_dir, "sitembk-hotel-en-us.0000.xml")
  try:
    with open(out_path, "wb") as f:
      f.write(xml_bytes)
    log.info("Saved sitemap XML: %s (%d bytes)", out_path, len(xml_bytes))
  except Exception as e:
    log.debug("Failed saving sitemap XML: %s", e)

  return out


def _strip_ns(tag: str) -> str:
  """Strip XML namespace from a tag name."""
  return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def iter_sitemap_urls(xml_path: str) -> Iterator[Dict[str, str]]:
  """Stream-parse a sitemap XML (or .gz) yielding dicts with loc/lastmod/changefreq.

  Uses ElementTree.iterparse for O(1) memory regardless of file size.
  """
  # Open as gzip if needed
  opener = gzip.open if xml_path.endswith('.gz') else open
  with opener(xml_path, 'rb') as fh:
    context = ET.iterparse(fh, events=("end",))
    # prime the iterator and store root to help free memory
    try:
      _, root = next(context)
    except StopIteration:
      return

    for event, elem in context:
      if _strip_ns(elem.tag) != 'url':
        continue

      rec: Dict[str, str] = {}
      for child in list(elem):
        key = _strip_ns(child.tag)
        if key in ("loc", "lastmod", "changefreq") and child.text:
          rec[key] = child.text.strip()

      if rec.get("loc"):
        yield rec

      # free element memory as we go
      elem.clear()
      # also clear root periodically to release processed nodes
      if len(root) > 1000:
        root.clear()


def export_sitemap_urls_to_ndjson(xml_path: str, out_path: Optional[str] = None) -> str:
  """Export sitemap entries to NDJSON under artifacts and return the path.

  - Writes one JSON object per line: {loc, lastmod, changefreq}
  - Creates the artifacts directory if needed.
  """
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass

  if out_path is None:
    base = os.path.splitext(os.path.basename(xml_path))[0]
    out_path = os.path.join(artifact_dir, f"{base}.ndjson")

  count = 0
  with open(out_path, 'w', encoding='utf-8') as out_f:
    for rec in iter_sitemap_urls(xml_path):
      out_f.write(json.dumps(rec, ensure_ascii=False))
      out_f.write("\n")
      count += 1

  log.info("Exported %d sitemap entries to %s", count, out_path)
  return out_path
