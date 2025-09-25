import gzip
import logging
import os
import re
import time
from typing import Dict, List, Optional

import requests
import xml.etree.ElementTree as ET


log = logging.getLogger(__name__)

ROBOTS_URL = "https://www.booking.com/robots.txt"
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}
RETRYABLE_STATUS_CODES = {202, 429, 500, 502, 503, 504}


def _resolve_proxies() -> Dict[str, str]:
    proxy = os.getenv("BOOKING_HTTPS_PROXY") or os.getenv("BOOKING_HTTP_PROXY")
    if not proxy:
        return {}

    log.info("Booking sitemap requests using HTTPS proxy configuration")
    return {"https": proxy}


def _create_session(with_proxy: bool = True) -> requests.Session:
    session = requests.Session()
    session.headers.update(HTTP_HEADERS)

    if with_proxy:
        proxies = _resolve_proxies()
        if proxies:
            session.trust_env = False
            session.proxies.update(proxies)

    return session


def _request_with_retry(session: requests.Session, url: str, *, timeout: int = 30, max_attempts: int = 3) -> Optional[requests.Response]:
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            log.warning("request attempt %s failed for %s: %s", attempt, url, exc)
        else:
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_attempts:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    backoff = max(backoff, float(retry_after))
                log.info("request attempt %s for %s returned %s; retrying after %.1fs", attempt, url, response.status_code, backoff)
            else:
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    return response
                log.warning("request attempt %s for %s returned %s; no more retries", attempt, url, response.status_code)
                return None

        if attempt < max_attempts:
            time.sleep(backoff)
            backoff *= 2

    return None


def fetch_robots_sitemaps(robots_url: str = ROBOTS_URL) -> List[str]:
    """Return every sitemap URL declared in robots.txt."""
    session = _create_session(with_proxy=True)
    response = _request_with_retry(session, robots_url)
    print('🚀 ~ response:', response)
    if response is None:
        log.warning("robots fetch failed after retries")
        return []

    return re.findall(r"^Sitemap:\s*(\S+)$", response.text, re.MULTILINE | re.IGNORECASE)


def select_hotel_index(sitemap_urls: List[str]) -> Optional[str]:
    """Pick the Booking.com hotel sitemap index URL, prioritising NL locales."""
    for candidate in sitemap_urls:
        if "sitembk-hotel-nl" in candidate and "index" in candidate:
            return candidate

    for candidate in sitemap_urls:
        if "sitembk-hotel" in candidate and "index" in candidate:
            return candidate

    return None


def get_hotel_sitemap_index() -> Optional[str]:
    """Fetch robots.txt and return the preferred hotel sitemap index URL."""
    sitemap_urls = fetch_robots_sitemaps()
    print('🚀 ~ sitemap_urls:', sitemap_urls)
    return select_hotel_index(sitemap_urls)


def get_en_us_sitemap_entries(index_url: str) -> List[Dict[str, Optional[str]]]:
    print('🚀 ~ index_url:', index_url)
    """Return child sitemap entries (loc/lastmod) from the given index."""
    session = _create_session()
    response = _request_with_retry(session, index_url)
    if response is None:
        log.warning("sitemap index fetch failed after retries")
        return []

    content = response.content
    if index_url.endswith(".gz") or "gzip" in response.headers.get("Content-Type", "").lower():
        try:
            content = gzip.decompress(content)
        except OSError:
            pass

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        log.warning("sitemap XML parse failed: %s", exc)
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries: List[Dict[str, Optional[str]]] = []
    for node in root.findall("sm:sitemap", ns):
        loc_el = node.find("sm:loc", ns)
        lastmod_el = node.find("sm:lastmod", ns)
        # if 'en-us' not in loc_el.text.strip() or loc_el is None or not (loc_el.text or "").strip():
        #     continue
        if loc_el is None or not loc_el.text:
            continue

        loc_text = loc_el.text.strip()
        if "en-us" not in loc_text:
            continue

        entries.append({
            "loc": loc_text,
            "lastmod": (lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None),
        })

    return entries


def download_sitemap(entry: Dict[str, Optional[str]], xml_dir: str) -> str:
    """Download a single child sitemap (.xml or .xml.gz) and return the saved path."""
    os.makedirs(xml_dir, exist_ok=True)

    url = entry.get("loc")
    if not url:
        raise ValueError("sitemap entry missing 'loc'")

    filename = os.path.basename(url)
    if filename.endswith(".gz"):
        filename = filename[:-3]

    dest_path = os.path.join(xml_dir, filename)

    session = _create_session()
    response = _request_with_retry(session, url)
    if response is None:
        raise ValueError(f"sitemap download failed after retries for {url}")

    payload = response.content
    if url.endswith(".gz") or "gzip" in response.headers.get("Content-Type", "").lower():
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass

    with open(dest_path, "wb") as handle:
        handle.write(payload)

    log.info("Saved sitemap XML: %s (%d bytes)", dest_path, len(payload))
    return dest_path
