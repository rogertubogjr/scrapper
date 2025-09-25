import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scheduler.jobs import (
    crawl_popular,
    ingest_booking_sitemaps,
    materialize_booking_sitemaps_job,
)


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def _crawl_popular_job() -> None:
    # Run blocking job in a thread to keep the event loop responsive
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, crawl_popular)


async def _booking_sitemap_ingest_job() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, ingest_booking_sitemaps)


async def _booking_sitemap_materialize_job() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, materialize_booking_sitemaps_job)


async def main() -> None:
    _configure_logging()
    log = logging.getLogger("scheduler")

    # Default to hourly: minute 0, every hour (UTC)
    popular_cron_expr = os.getenv("CRON_POPULAR", "0 * * * *")
    booking_materialize_cron_expr = os.getenv("CRON_BOOKING_SITEMAP_MATERIALIZE", "0 * * * *")
    booking_cron_expr = os.getenv("CRON_BOOKING_SITEMAP", "0 * * * *")

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _crawl_popular_job,
        CronTrigger.from_crontab(popular_cron_expr, timezone="UTC"),
        id="crawl_popular",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    # scheduler.add_job(
    #     _booking_sitemap_materialize_job,
    #     CronTrigger.from_crontab(booking_materialize_cron_expr, timezone="UTC"),
    #     id="materialize_booking_sitemaps",
    #     max_instances=1,
    #     coalesce=True,
    #     replace_existing=True,
    # )
    # scheduler.add_job(
    #     _booking_sitemap_ingest_job,
    #     CronTrigger.from_crontab(booking_cron_expr, timezone="UTC"),
    #     id="ingest_booking_sitemaps",
    #     max_instances=1,
    #     coalesce=True,
    #     replace_existing=True,
    # )
    scheduler.start()

    log.info(
        "Scheduler started (UTC) with CRON_POPULAR='%s', CRON_BOOKING_SITEMAP_MATERIALIZE='%s', CRON_BOOKING_SITEMAP='%s'",
        popular_cron_expr,
        booking_materialize_cron_expr,
        booking_cron_expr,
    )

    try:
        # Keep the event loop alive indefinitely until interrupted
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler shutting down...")
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
