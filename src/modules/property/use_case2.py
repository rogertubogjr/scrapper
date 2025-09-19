import asyncio
import logging
from typing import Any, Dict, List

from flask import current_app
from playwright.async_api import async_playwright

log = logging.getLogger(__name__)


def run_async(coro):
    """Run async coroutine from sync context safely."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def run_playwright() -> Dict[str, Any]:
    """Playwright flow with config-driven headless and explicit waits.

    Reads config from Flask `current_app.config`:
      - PLAYWRIGHT_HEADLESS: bool (default True)
      - PLAYWRIGHT_ARGS: list of chromium args
    """
    cfg = current_app.config if current_app else {}
    headless = bool(cfg.get("PLAYWRIGHT_HEADLESS", True))
    chromium_args = cfg.get("PLAYWRIGHT_ARGS") or [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
    ]

    url = (
        "https://www.booking.com/searchresults.html?ss=cebu&search_selected=true&"
        "checkin=2025-10-10&checkout=2025-10-11&group_adults=2&no_rooms=1&group_children=0"
    )

    # Use context managers to ensure proper tear-down
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless, args=chromium_args)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.5845.110 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")

        # Prefer explicit waits over fixed timeouts
        await page.wait_for_selector('input[type="checkbox"]', timeout=20000)

        # Extract the filter information
        results: List[Dict[str, str]] = await page.evaluate(
            """
            () => Array.from(document.querySelectorAll('input[type="checkbox"]'))
                .filter(el => {
                    const aria = el.getAttribute('aria-label');
                    return el.name && el.value && aria && aria.trim() !== '';
                })
                .map(el => ({
                    name: el.name,
                    value: el.value,
                    ariaLabel: el.getAttribute('aria-label').trim()
                }))
            """
        )

        # Close resources in reverse order
        await context.close()
        await browser.close()

    log.debug("Collected %d checkbox filters", len(results))
    return {
        "count": len(results),
        "filters": results[:50],  # return a subset to keep payload small
        "headless": headless,
    }


def get_properties_v2() -> Dict[str, Any]:
    """Synchronous entrypoint returning structured results."""
    data = run_async(run_playwright())
    return data

