import gzip
import json
import logging
import os
from typing import Dict, Iterator, Optional
import xml.etree.ElementTree as ET


log = logging.getLogger(__name__)


def _strip_ns(tag: str) -> str:
    """Strip XML namespace from a tag name."""
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def iter_sitemap_urls(xml_path: str) -> Iterator[Dict[str, str]]:
    """Stream-parse a sitemap XML (or .gz) yielding {loc,lastmod,changefreq}."""
    opener = gzip.open if xml_path.endswith('.gz') else open
    with opener(xml_path, 'rb') as handle:
        context = ET.iterparse(handle, events=("end",))
        try:
            _, root = next(context)
        except StopIteration:
            return

        for _event, elem in context:
            if _strip_ns(elem.tag) != 'url':
                continue

            record: Dict[str, str] = {}
            for child in list(elem):
                key = _strip_ns(child.tag)
                if key in {"loc", "lastmod", "changefreq"} and child.text:
                    record[key] = child.text.strip()

            if record.get("loc"):
                yield record

            elem.clear()
            if len(root) > 1000:
                root.clear()


def export_sitemap_urls_to_ndjson(xml_path: str, *, output_dir: Optional[str] = None, out_path: Optional[str] = None) -> str:
    """Export sitemap entries to NDJSON and return the written file path."""
    if out_path is None:
        if output_dir is None:
            raise ValueError("either output_dir or out_path must be provided")
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(xml_path))[0]
        out_path = os.path.join(output_dir, f"{base}.ndjson")
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    count = 0
    with open(out_path, 'w', encoding='utf-8') as destination:
        for record in iter_sitemap_urls(xml_path):
            destination.write(json.dumps(record, ensure_ascii=False))
            destination.write("\n")
            count += 1

    log.info("Exported %d sitemap entries to %s", count, out_path)
    return out_path

