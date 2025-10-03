"""Helpers for scoring crawled properties with LLM agents."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import time
from typing import Any, Dict, Sequence, Tuple

from src.agent_helpers.property_keyword_scorer import property_keyword_scorer

from .agent_runner import run_agent_action
from .async_runner import run_async

log = logging.getLogger(__name__)


def score_properties(items: Sequence[Dict[str, Any]], key_terms: Sequence[str]) -> Dict[str, Any]:
  """Populate keyword scores for each property item using the keyword scorer agent.

  Args:
    items: Crawl items that may include summary information and optional page_data.
    key_terms: Ordered list of prompt-derived key terms to evaluate.

  Returns:
    Dictionary with aggregate telemetry such as number of scored jobs and total duration.
  """
  if not key_terms:
    return {"jobs": 0, "duration_ms": 0, "max_item_ms": 0}

  scoring_jobs: list[Tuple[int, str | None, str]] = []
  for idx, crawled_item in enumerate(items):
    page_data_for_agent: Dict[str, Any] | None = None
    original_page_data = crawled_item.get("page_data")
    if isinstance(original_page_data, dict):
      page_data_for_agent = copy.deepcopy(original_page_data)
      page_data_for_agent.pop("property_description", None)

    property_payload = {
      "summary": {
        "title": crawled_item.get("title"),
        "location": crawled_item.get("location"),
        "rating_reviews": crawled_item.get("rating_reviews"),
        "room_info": crawled_item.get("room_info"),
        "price": crawled_item.get("price"),
        "fees": crawled_item.get("fees"),
      },
      "page_data": page_data_for_agent,
    }

    scorer_input = json.dumps(
      {
        "property_payload": property_payload,
        "key_terms": key_terms,
      },
      ensure_ascii=False,
    )
    scoring_jobs.append((idx, crawled_item.get("link"), scorer_input))

  if not scoring_jobs:
    return {"jobs": 0, "duration_ms": 0, "max_item_ms": 0}

  async def _score_all():
    semaphore = asyncio.Semaphore(4)

    async def _score(idx: int, link: str | None, payload: str):
      async with semaphore:
        started = time.monotonic()
        try:
          result = await run_agent_action(payload, property_keyword_scorer, None, False)
          duration_ms = int((time.monotonic() - started) * 1000)
          log.debug("keyword scoring item completed; link=%s duration_ms=%d", link, duration_ms)
          return idx, result, duration_ms
        except Exception as exc:  # pragma: no cover - operational telemetry
          log.warning("keyword scoring failed for %s: %s", link, exc)
          return idx, None, 0

    return await asyncio.gather(
      *[_score(idx, link, payload) for idx, link, payload in scoring_jobs]
    )

  scoring_started = time.monotonic()
  scoring_results = run_async(_score_all())
  total_duration_ms = int((time.monotonic() - scoring_started) * 1000)

  max_item_ms = 0
  for idx, result, item_duration in scoring_results:
    if item_duration > max_item_ms:
      max_item_ms = item_duration
    if isinstance(result, dict):
      result.pop("cleaned_payload", None)
      items[idx]["property_score"] = result

  log.debug(
    "keyword scoring completed; jobs=%d duration_ms=%d max_item_ms=%d",
    len(scoring_jobs),
    total_duration_ms,
    max_item_ms,
  )
  return {"jobs": len(scoring_jobs), "duration_ms": total_duration_ms, "max_item_ms": max_item_ms}
