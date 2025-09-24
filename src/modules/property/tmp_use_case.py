import os, json, re, asyncio, logging, time, gzip, requests
from base64 import b64decode
from typing import Any, Dict, List, Iterator, Optional
from crawl4ai import (
  AsyncWebCrawler,
  BrowserConfig,
  CrawlerRunConfig,
  JsonXPathExtractionStrategy,
  MemoryAdaptiveDispatcher,
)
from agents import Runner
from datetime import date, timedelta
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from flask import current_app
from playwright.async_api import async_playwright
from src.agent_helpers.destination_extractor import ah_destination_extractor
from src.agent_helpers.booking_search_url_agent import booking_search_url_agent
from src.handler.error_handler import InvalidDataError, NotFoundError, UnexpectedError

log = logging.getLogger(__name__)
HTTP_HEADERS = {
  "User-Agent": (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
  )
}

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

async def run_crawler(urls) -> Dict[str, Any]:
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
    scan_full_page=True
  )
  dispatcher = MemoryAdaptiveDispatcher(
      memory_threshold_percent=70.0,
      max_session_permit=10
  )

  async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
    results = await crawler.arun_many(
      urls=urls,
      config=config,
      dispatcher=dispatcher
    )

    # if not result.success:
    #   log.warning("Crawl failed: %s", result.error_message)

    url_and_locations = []

    for res in results:
      if res.success and len(res.extracted_content):

        raw = res.extracted_content or "[]"
        data = json.loads(raw)
        if isinstance(data, list):
          for x in data:
            if isinstance(x, dict):
              location = x.get("location").split('After booking')[0].split('Excellent location')[0]
              url_and_locations.append(dict(location = location, url = res.url))
      else:
        print("Failed:", res.url, "-", res.error_message)

    return url_and_locations


def get_hotel_sitemap_url():
  url = "https://www.booking.com/robots.txt"

  try:
    resp = requests.get(url, timeout=15, headers=HTTP_HEADERS)
    resp.raise_for_status()
  except requests.RequestException as e:
    log.warning("robots fetch failed: %s", e)
    return []

  sitemap_urls = re.findall(r"^Sitemap:\s*(\S+)$", resp.text, re.MULTILINE | re.IGNORECASE)

  # Prefer NL hotel sitemap index if present
  index_url = None
  for sm_url in sitemap_urls:
    if "sitembk-hotel-nl" in sm_url and "index" in sm_url:
      index_url = sm_url
      break
  if not index_url:
    for sm_url in sitemap_urls:
      if "sitembk-hotel" in sm_url and "index" in sm_url:
        index_url = sm_url
        break

  return index_url

def get_en_us_hotel_xml(index_url):
  resp = requests.get(index_url, timeout=20, headers=HTTP_HEADERS)
  resp.raise_for_status()
  content = resp.content
  if index_url.endswith(".gz") or "gzip" in resp.headers.get("Content-Type", "").lower():
    try:
      content = gzip.decompress(content)
    except OSError:
      pass

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

  return out

def thread_download_and_save_xml_gz(params):
  url = params['loc']
  filename = url.split('/')[3].replace('.gz','')
  # Download the gzip sitemap and save decompressed XML to /tmp
  try:
    resp = requests.get(url, timeout=30, headers=HTTP_HEADERS)
    resp.raise_for_status()
    gz_bytes = resp.content
  except requests.RequestException as e:
    log.warning("gz sitemap fetch failed: %s", e)
    return None

  # Decompress .gz → XML bytes (fallback if server sends plain XML)
  try:
    xml_bytes = gzip.decompress(gz_bytes)
  except OSError:
    xml_bytes = gz_bytes

  # Persist for inspection under artifacts directory
  sitemap_dir = os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "/app/sitemap_data"))
  try:
    os.makedirs(f"{sitemap_dir}/xml", exist_ok=True)
  except Exception:
    pass
  out_path = os.path.join(f"{sitemap_dir}/xml", filename)
  try:
    with open(out_path, "wb") as f:
      f.write(xml_bytes)
    log.info("Saved sitemap XML: %s (%d bytes)", out_path, len(xml_bytes))
  except Exception as e:
    log.debug("Failed saving sitemap XML: %s", e)

  return filename

def thread_worker(param_filename):
  sitemap_dir = os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "/app/sitemap_data"))
  export_sitemap_urls_to_ndjson(f"{sitemap_dir}/xml/{param_filename}")
  return param_filename

def export_sitemap_ndjson():
  sitemap_dir = os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "/app/sitemap_data"))

  sitemap_index_url = get_hotel_sitemap_url()
  en_us_sitemap_entries = get_en_us_hotel_xml(sitemap_index_url)

  with ThreadPoolExecutor(max_workers=int(os.getenv('SITEMAP_WORKER_THREADS'))) as executor:
    sitemap_xml_filenames = list(executor.map(thread_download_and_save_xml_gz, en_us_sitemap_entries[0:1]))

  with ThreadPoolExecutor(max_workers=int(os.getenv('SITEMAP_WORKER_THREADS'))) as executor:
    list(executor.map(thread_worker, sitemap_xml_filenames))

  # crawl = run_async(run_crawler(urls_to_scrape))

  # List and sort all NDJSON files under sitemap_data/ndjson
  ndjson_dir = os.path.join(sitemap_dir, "ndjson")
  try:
    ndjson_files = [
      os.path.join(ndjson_dir, name)
      for name in os.listdir(ndjson_dir)
      if name.endswith('.ndjson')
    ]
  except FileNotFoundError:
    ndjson_files = []

  # Sort by filename (ascending)
  ndjson_files_by_name = sorted(ndjson_files)

  for file_path in ndjson_files_by_name:

    urls_to_scrape_groups = []
    group_limit_counter = 0

    with open(file_path, encoding="utf-8") as f:
      group_counter = 0
      urls_to_scrape = []

      for line in f:
        group_counter += 1
        if not line.strip():
          continue
        rec = json.loads(line)
        urls_to_scrape.append(rec["loc"])
        if group_counter == int(os.getenv('PARALLEL_URL_TO_SCRAPE')):
          urls_to_scrape_groups.append(urls_to_scrape)
          group_counter = 0
          urls_to_scrape = []
          group_limit_counter += 1

        if group_limit_counter == 2:
          break

    for i in urls_to_scrape_groups:
      print(i)

    break



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
  sitemap_dir = os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "artifacts")) + '/ndjson'
  try:
    os.makedirs(f"{sitemap_dir}", exist_ok=True)
  except Exception:
    pass

  if out_path is None:
    base = os.path.splitext(os.path.basename(xml_path))[0]
    out_path = os.path.join(f"{sitemap_dir}", f"{base}.ndjson")

  count = 0
  with open(out_path, 'w', encoding='utf-8') as out_f:
    for rec in iter_sitemap_urls(xml_path):
      out_f.write(json.dumps(rec, ensure_ascii=False))
      out_f.write("\n")
      count += 1

  log.info("Exported %d sitemap entries to %s", count, out_path)
  return out_path
