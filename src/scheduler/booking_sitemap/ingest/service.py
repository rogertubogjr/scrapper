"""Read Booking sitemap NDJSON files and ingest hotel listings."""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from typing import List, Sequence

from . import crawler
from src.scheduler.booking_sitemap.utils import get_env_int, resolve_dirs
from src.db.models.hotel_listing import HotelListing


log = logging.getLogger(__name__)

# Public entry point → helper chain
# ingest_booking_sitemaps_from_ndjson()
#   ↳ resolve_dirs() (from utils)
#   ↳ _process_ndjson_files()
#         ↳ _load_url_groups()
#         ↳ _ingest_groups()
#             ↳ _filter_existing()
#             ↳ crawler.run_crawler()


def ingest_booking_sitemaps_from_ndjson(*, max_groups: int = 2) -> None:
    """Process prepared NDJSON files and ingest new Booking listings."""
    _base_dir, _xml_dir, ndjson_dir = resolve_dirs()
    group_size = get_env_int('PARALLEL_URL_TO_SCRAPE', 10)
    _process_ndjson_files(ndjson_dir, group_size=group_size, max_groups=max_groups)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _process_ndjson_files(ndjson_dir: str, *, group_size: int, max_groups: int) -> None:
    try:
        ndjson_files = [
            os.path.join(ndjson_dir, name)
            for name in os.listdir(ndjson_dir)
            if name.endswith('.ndjson')
        ]
    except FileNotFoundError:
        return

    for ndjson_path in sorted(ndjson_files):
        groups = _load_url_groups(ndjson_path, group_size=group_size, max_groups=max_groups)
        if groups:
            _ingest_groups(groups)
            break

def _load_url_groups(ndjson_path: str, *, group_size: int, max_groups: int) -> List[List[str]]:
    if group_size <= 0:
        group_size = 1

    groups: List[List[str]] = []
    with open(ndjson_path, encoding="utf-8") as handle:
        batch: List[str] = []
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            loc = record.get("loc")
            if not loc:
                continue
            batch.append(loc)
            if len(batch) == group_size:
                groups.append(batch)
                batch = []
                if len(groups) >= max_groups:
                    break
    return groups

def _ingest_groups(groups: Sequence[Sequence[str]]) -> None:
    for urls in groups:
        new_urls = _filter_existing(urls)
        if not new_urls:
            continue

        crawled = crawler.run_async(crawler.run_crawler(new_urls))
        if not crawled:
            continue

        rows = []
        new_urls_logged: List[str] = []
        for item in crawled:
            url_val = item.get('url')
            loc_val = item.get('location')
            if not url_val:
                continue
            rows.append({
                'hotel_url': url_val,
                'location': loc_val,
                'lastmod': date.today(),
                'origin': 'booking.com',
            })
            new_urls_logged.append(url_val)

        if rows:
            inserted_count = HotelListing.bulk_upsert(rows)
            if inserted_count:
                log.info(
                    "Inserted %s hotel listings: %s",
                    inserted_count,
                    new_urls_logged,
                )

def _filter_existing(urls: Sequence[str]) -> List[str]:
    if not urls:
        return []

    existing = {
        url
        for (url,) in (
            HotelListing.query
            .with_entities(HotelListing.hotel_url)
            .filter(
                HotelListing.hotel_url.in_(urls),
                HotelListing.origin == 'booking.com',
            )
            .all()
        )
    }
    return [url for url in urls if url not in existing]

