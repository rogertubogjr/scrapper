import asyncio
import logging
import os
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
    # Read flags from Flask config, with environment fallbacks so we don't
    # require instance/config.py entries in all environments.
    def _get_bool(name: str, default: bool) -> bool:
        v = cfg.get(name)
        if v is None:
            v = os.getenv(name)
        if v is None:
            return default
        return str(v).strip().lower() in {"1", "true", "yes", "on"}

    stealth = _get_bool("PLAYWRIGHT_STEALTH", True)
    debug_artifacts = _get_bool("PLAYWRIGHT_DEBUG_ARTIFACTS", False)
    artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", "/tmp")

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
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        # Light stealth: hide webdriver flag
        if stealth:
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        # Allow network to settle a bit
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # Try to accept cookie banners if present
        async def try_accept_cookies() -> None:
            try:
                sel = (
                    "#onetrust-accept-btn-handler, "
                    "button:has-text('Accept all'), "
                    "button:has-text('Accept'), "
                    "button:has-text('I agree'), "
                    "button[aria-label*='Accept']"
                )
                btn = page.locator(sel).first
                # Use locator() API's first() method
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    await btn.click(timeout=3000)
            except Exception:
                # Non-fatal; proceed
                pass

        await try_accept_cookies()

        # Prefer specific filters container; fallback to any checkbox
        try:
            await page.wait_for_selector(
                "[data-filters-group] input[type=checkbox], input[type=checkbox][name][value]",
                timeout=20000,
            )
        except Exception:
            # still continue to evaluate; may produce zero results
            pass

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
                    ariaLabel: el.getAttribute('aria-label')?.trim() || ''
                }))
            """
        )

        # If empty in production/headless, capture debug artifacts
        if debug_artifacts and len(results) == 0:
            try:
                # Ensure artifact directory exists
                try:
                    os.makedirs(artifact_dir, exist_ok=True)
                except Exception:
                    pass
                await page.screenshot(path=f"{artifact_dir}/properties_screenshot.png", full_page=True)
                html = await page.content()
                snippet = html[:100000]
                with open(f"{artifact_dir}/properties_snippet.html", "w", encoding="utf-8") as f:
                    f.write(snippet)
                title = await page.title()
                log.debug(
                    "Saved debug artifacts: title=%s screenshot=%s snippet=%s",
                    title,
                    f"{artifact_dir}/properties_screenshot.png",
                    f"{artifact_dir}/properties_snippet.html",
                )
            except Exception as e:
                log.debug("Failed to save debug artifacts: %s", e)

        # Close resources in reverse order
        await context.close()
        await browser.close()

    log.debug("Collected %d checkbox filters", len(results))
    return {
        "count": len(results),
        "filters": results[:50],  # return a subset to keep payload small
        "headless": headless,
    }


def get_properties() -> Dict[str, Any]:
    """Synchronous entrypoint returning structured results."""
    data = run_async(run_playwright())
    return data
