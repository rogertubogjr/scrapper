import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import List, Sequence

from src.scheduler.booking_sitemap import crawler, parser, sources
from src.db.models.hotel_listing import HotelListing


log = logging.getLogger(__name__)


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_sitemap_base_dir() -> str:
    return os.getenv("SITEMAP_DIR", os.path.join(os.getcwd(), "/app/sitemap_data"))


def _resolve_dirs() -> tuple[str, str, str]:
    base_dir = _get_sitemap_base_dir()
    xml_dir = os.path.join(base_dir, "xml")
    ndjson_dir = os.path.join(base_dir, "ndjson")
    os.makedirs(xml_dir, exist_ok=True)
    os.makedirs(ndjson_dir, exist_ok=True)
    return base_dir, xml_dir, ndjson_dir


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
        # Match previous behaviour: ignore partial batches
    return groups


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


def export_sitemap_ndjson() -> None:
    base_dir, xml_dir, ndjson_dir = _resolve_dirs()
    log.debug("Using sitemap directory %s", base_dir)

    index_url = sources.get_hotel_sitemap_index()
    if not index_url:
        log.warning("No hotel sitemap index found")
        return

    entries = sources.get_en_us_sitemap_entries(index_url)
    if not entries:
        log.info("No en-us sitemap entries discovered from %s", index_url)
        return

    worker_threads = _get_env_int('SITEMAP_WORKER_THREADS', 4)
    subset = entries[:1]

    def _download(entry):
        return sources.download_sitemap(entry, xml_dir)

    with ThreadPoolExecutor(max_workers=worker_threads) as executor:
        xml_paths = list(executor.map(_download, subset))

    def _to_ndjson(xml_path):
        return parser.export_sitemap_urls_to_ndjson(xml_path, output_dir=ndjson_dir)

    with ThreadPoolExecutor(max_workers=worker_threads) as executor:
        list(executor.map(_to_ndjson, xml_paths))

    group_size = _get_env_int('PARALLEL_URL_TO_SCRAPE', 10)
    _process_ndjson_files(ndjson_dir, group_size=group_size, max_groups=2)
