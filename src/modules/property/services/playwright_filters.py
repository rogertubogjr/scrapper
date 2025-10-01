"""Playwright utilities for extracting checkbox filters from Booking search pages."""

import os
from typing import Any, Dict, List

from playwright.async_api import async_playwright

from .config import _get_bool, _get_str


async def run_playwright(url: str) -> Dict[str, Any]:
  """Scrape availability links using raw Playwright."""
  headless = _get_bool("PLAYWRIGHT_HEADLESS", True)
  artifact_dir = os.getenv("PLAYWRIGHT_ARTIFACT_DIR", os.path.join(os.getcwd(), "artifacts"))
  try:
    os.makedirs(artifact_dir, exist_ok=True)
  except Exception:
    pass

  items: List[Dict[str, str]] = []

  proxy_server = _get_str("PLAYWRIGHT_PROXY_SERVER")
  proxy_username = _get_str("PLAYWRIGHT_PROXY_USERNAME")
  proxy_password = _get_str("PLAYWRIGHT_PROXY_PASSWORD")
  proxy_enabled = _get_bool("PROXY_ENABLED", False)

  proxy_settings = None
  if proxy_enabled and proxy_server:
    proxy_settings = {"server": proxy_server}
    if proxy_username:
      proxy_settings["username"] = proxy_username
    if proxy_password:
      proxy_settings["password"] = proxy_password

  async with async_playwright() as pw:
    browser = await pw.chromium.launch(
      headless=headless,
      args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
      ],
      proxy=proxy_settings,
    )
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

    await context.add_init_script(
      "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )

    page = await context.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    try:
      await page.wait_for_load_state("networkidle", timeout=7000)
    except Exception:
      pass

    results = await page.evaluate("""() => {
            return Array.from(
            document.querySelectorAll('input[type=\"checkbox\"]')
            )
            .filter(el => {
            const aria = el.getAttribute('aria-label');
            return el.name && el.value && aria && aria.trim() !== '';
            })
            .map(el => ({
            name: el.name,
            value: el.value,
            ariaLabel: el.getAttribute('aria-label').trim()
            }));
        }""")

    checkbox_filter_code = ""

    for i in results:
      filter_name = i["ariaLabel"].split(":")[0]
      code = i["value"].replace("=", "%3D")
      checkbox_filter_code += f"• {filter_name} → {code}\n"

    await context.close()
    await browser.close()

    return checkbox_filter_code

  return {
    "count": len(items),
    "items": items,
    "source": "playwright",
    "headless": headless,
  }
