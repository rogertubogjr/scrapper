import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scheduler.jobs import crawl_popular


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def _crawl_popular_job() -> None:
    # Run blocking job in a thread to keep the event loop responsive
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, crawl_popular)


async def main() -> None:
    _configure_logging()
    log = logging.getLogger("scheduler")

    # Default to hourly: minute 0, every hour
    cron_expr = os.getenv("CRON_POPULAR", "* 1 * * *")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _crawl_popular_job,
        CronTrigger.from_crontab(cron_expr),
        id="crawl_popular",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.start()

    log.info("Scheduler started with CRON_POPULAR='%s'", cron_expr)

    try:
        # Keep the event loop alive indefinitely until interrupted
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler shutting down...")
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
