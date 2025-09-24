import gzip
import logging
import os
import re
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
    )
}


def fetch_robots_sitemaps(robots_url: str = ROBOTS_URL) -> List[str]:
    """Return every sitemap URL declared in robots.txt."""
    try:
        resp = requests.get(robots_url, timeout=15, headers=HTTP_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("robots fetch failed: %s", exc)
        return []

    return re.findall(r"^Sitemap:\s*(\S+)$", resp.text, re.MULTILINE | re.IGNORECASE)


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
    return select_hotel_index(sitemap_urls)


def get_en_us_sitemap_entries(index_url: str) -> List[Dict[str, Optional[str]]]:
    """Return child sitemap entries (loc/lastmod) from the given index."""
    try:
        resp = requests.get(index_url, timeout=30, headers=HTTP_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("sitemap index fetch failed: %s", exc)
        return []

    content = resp.content
    if index_url.endswith(".gz") or "gzip" in resp.headers.get("Content-Type", "").lower():
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
        print('pass',entries)
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

    try:
        resp = requests.get(url, timeout=30, headers=HTTP_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("sitemap download failed: %s", exc)
        raise

    payload = resp.content
    if url.endswith(".gz") or "gzip" in resp.headers.get("Content-Type", "").lower():
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass

    with open(dest_path, "wb") as handle:
        handle.write(payload)

    log.info("Saved sitemap XML: %s (%d bytes)", dest_path, len(payload))
    return dest_path

