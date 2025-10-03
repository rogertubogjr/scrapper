import asyncio, copy, time, logging, json
from datetime import date, timedelta
from typing import Any, Dict

from src.agent_helpers.destination_extractor import ah_destination_and_terms
from src.agent_helpers.booking_search_url_agent import booking_search_url_agent
from src.handler.error_handler import InvalidDataError, NotFoundError, UnexpectedError
from src.modules.property.services import (
  _get_bool,
  run_agent_action,
  run_async,
  run_crawler,
  crawl_per_page_currently,
  run_playwright,
  score_properties,
)

log = logging.getLogger(__name__)


def get_properties(prompt: str) -> Dict[str, Any]:
  """Extract destination from a free-form prompt using the agent."""
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
        run_agent_action(prompt, ah_destination_and_terms, None, False),
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
  except Exception as exc:
    duration_ms = int((time.monotonic() - started) * 1000)
    log.exception(
      "destination extraction failed; duration_ms=%d error=%s",
      duration_ms,
      exc,
    )
    raise UnexpectedError("Destination extraction failed.")

  destination = None
  key_terms = []
  if isinstance(destination_data, dict):
    destination = destination_data.get("destination")
    key_terms = destination_data.get("key_terms") or []

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
  print('\n\n********raw_filters', raw_filters, '\n\n')
  filters_map = _parse_checkbox_filters(raw_filters)
  filters_json = json.dumps(filters_map, ensure_ascii=False)
  print('\n\n filters_json', filters_json)

  url_agent = booking_search_url_agent(filters_json)
  url_data = run_async(run_agent_action(prompt, url_agent, None, False))
  if not isinstance(url_data, dict) or "url" not in url_data or not url_data["url"]:
    raise UnexpectedError("Failed to generate a search URL.")

  final_url = url_data["url"]

  print(f'\n\nfinal_url {final_url} \n\n')

  crawl = run_async(run_crawler(final_url))
  if not isinstance(crawl, dict):
    crawl = {
      "count": 0,
      "items": [],
      "source": "crawl4ai",
      "headless": _get_bool("PLAYWRIGHT_HEADLESS", True),
    }

  property_links = [parsed_item['link'] for parsed_item in crawl['items']]

  print(f'\n\n SCRAPING {len(property_links)} LINKS \n\n')

  per_page_data = run_async(crawl_per_page_currently(property_links))

  for idx, crawled_item in enumerate(crawl['items']):
    property_data = None
    for page_data in per_page_data:
      if crawled_item['link'] == page_data['url']:
        property_data = copy.deepcopy(page_data)
    if property_data:
      crawled_item['page_data'] = property_data
      crawled_item['location'] = property_data['location']
      del property_data['url']
      del crawled_item['page_data']['location']

  if key_terms:
    score_properties(crawl['items'], key_terms)

  crawl["destination"] = destination
  if key_terms:
    crawl["key_terms"] = key_terms
  crawl.pop("headless", None)
  crawl.pop("url", None)
  return crawl
