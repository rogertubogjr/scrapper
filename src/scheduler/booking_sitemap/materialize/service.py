"""Download Booking sitemap XML files and convert them to NDJSON."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from . import parser, sources

from ..utils import get_env_int, resolve_dirs


log = logging.getLogger(__name__)


def materialize_booking_sitemaps(*, limit: Optional[int] = None) -> List[str]:
    """Fetch Booking sitemap XML files and export each to NDJSON."""
    base_dir, xml_dir, ndjson_dir = resolve_dirs()
    log.debug("Using sitemap directory %s", base_dir)

    index_url = sources.get_hotel_sitemap_index()
    if not index_url:
        log.warning("No hotel sitemap index found")
        return []

    entries = sources.get_en_us_sitemap_entries(index_url)
    if not entries:
        log.info("No en-us sitemap entries discovered from %s", index_url)
        return []

    if limit is not None and limit > 0:
        entries = entries[:limit]

    worker_threads = get_env_int('SITEMAP_WORKER_THREADS', 4)

    def _download(entry):
        return sources.download_sitemap(entry, xml_dir)

    with ThreadPoolExecutor(max_workers=worker_threads) as executor:
        xml_paths = list(executor.map(_download, entries))

    def _to_ndjson(xml_path):
        return parser.export_sitemap_urls_to_ndjson(xml_path, output_dir=ndjson_dir)

    with ThreadPoolExecutor(max_workers=worker_threads) as executor:
        ndjson_paths = list(executor.map(_to_ndjson, xml_paths))

    log.info("Materialized %d sitemap files to NDJSON", len(ndjson_paths))
    return ndjson_paths
