"""Asyncio gather-based variant of property scoring helpers."""

from __future__ import annotations

import asyncio, time, copy, json, logging
from typing import Any, Dict, Sequence, Tuple

from src.agent_helpers.property_keyword_scorer import property_keyword_scorer

from .agent_runner import run_agent_action
from .async_runner import run_async

log = logging.getLogger(__name__)


def score_properties(items: Sequence[Dict[str, Any]], key_terms: Sequence[str]) -> Dict[str, Any]:
  start = time.perf_counter()
  """Populate keyword scores using asyncio.gather for parallel execution."""
  if not key_terms:
    return {"jobs": 0}

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
    return {"jobs": 0}

  async def _score_all():
    async def _score(idx: int, link: str | None, payload: str):
      try:
        result = await run_agent_action(payload, property_keyword_scorer, None, False)
        log.debug("keyword scoring item completed; link=%s", link)
        return idx, result
      except Exception as exc:
        log.warning("keyword scoring failed for %s: %s", link, exc)
        return idx, None

    tasks = [_score(idx, link, payload) for idx, link, payload in scoring_jobs]
    return await asyncio.gather(*tasks)

  scoring_results = run_async(_score_all())

  for idx, result in scoring_results:
    if isinstance(result, dict):
      result.pop("cleaned_payload", None)
      total_score = 0
      terms = result.get("terms")
      if isinstance(terms, list):
        for term in terms:
          if not isinstance(term, dict):
            continue
          score_value = term.get("score")
          if isinstance(score_value, (int, float)):
            total_score += int(score_value)
          elif isinstance(score_value, str):
            stripped = score_value.strip()
            if stripped:
              try:
                total_score += int(float(stripped))
              except ValueError:
                continue
      result["total_score"] = total_score
      items[idx]["property_score"] = result

  log.debug("keyword scoring completed (gather); jobs=%d", len(scoring_jobs))
  end = time.perf_counter()

  print(f"\n\n\n Execution time: {end - start:.6f} seconds \n\n")
  return {"jobs": len(scoring_jobs)}
