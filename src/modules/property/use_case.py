import asyncio
from playwright.async_api import async_playwright


def run_async(coro):
    """Helper function to run async code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def run_playwright():
  playwright = await async_playwright().start()
  browser = await playwright.chromium.launch(
                headless=False,  # Set to True for headless mode
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

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

  await page.goto('https://www.booking.com/searchresults.html?ss=cebu&search_selected=true&checkin=2025-10-10&checkout=2025-10-11&group_adults=2&no_rooms=1&group_children=0', wait_until="domcontentloaded")
  await page.wait_for_timeout(30000)

  results = await page.evaluate("""() => {
    return Array.from(
      document.querySelectorAll('input[type="checkbox"]')
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

  print(len(results))

  try:
      await context.close()
      await browser.close()
      await playwright.stop()
  except Exception as e:
      print(f"Error during cleanup: {str(e)}")


def get_properties():
  url = run_async(run_playwright())

  return dict(message = 'YEs')