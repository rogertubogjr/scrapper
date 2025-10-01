"""Utilities for executing async coroutines from synchronous contexts."""

import asyncio
from typing import Optional

_RUNNER_LOOP: Optional[asyncio.AbstractEventLoop] = None


def run_async(coro):
  """Run coroutine on a persistent event loop when no loop is active."""
  try:
    running_loop = asyncio.get_running_loop()
  except RuntimeError:
    running_loop = None

  if running_loop and running_loop.is_running():
    raise RuntimeError("run_async cannot execute inside an active event loop")

  global _RUNNER_LOOP
  if _RUNNER_LOOP is None or _RUNNER_LOOP.is_closed():
    _RUNNER_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(_RUNNER_LOOP)

  return _RUNNER_LOOP.run_until_complete(coro)
