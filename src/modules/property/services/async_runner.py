"""Utilities for executing async coroutines from synchronous contexts."""

import asyncio
import threading
from typing import Optional

_THREAD_LOCAL: threading.local = threading.local()


def _get_thread_loop() -> asyncio.AbstractEventLoop:
  loop: Optional[asyncio.AbstractEventLoop] = getattr(_THREAD_LOCAL, "loop", None)
  if loop is None or loop.is_closed():
    loop = asyncio.new_event_loop()
    _THREAD_LOCAL.loop = loop
  return loop


def run_async(coro):
  """Run coroutine on a thread-local event loop to allow concurrent requests."""
  try:
    running_loop = asyncio.get_running_loop()
  except RuntimeError:
    running_loop = None

  if running_loop and running_loop.is_running():
    raise RuntimeError("run_async cannot execute inside an active event loop")

  loop = _get_thread_loop()
  asyncio.set_event_loop(loop)
  return loop.run_until_complete(coro)
