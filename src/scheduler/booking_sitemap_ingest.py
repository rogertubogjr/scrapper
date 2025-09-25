"""Booking.com sitemap ingest entry points.

This module forwards to the dedicated booking_sitemap package so existing
imports keep working."""

from src.scheduler.booking_sitemap import (
    ingest_booking_sitemaps_from_ndjson,
    materialize_booking_sitemaps,
)

__all__ = [
    "ingest_booking_sitemaps_from_ndjson",
    "materialize_booking_sitemaps",
]
