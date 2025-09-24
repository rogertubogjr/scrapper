"""Booking.com sitemap ingest entry points.

This module forwards to the dedicated booking_sitemap package so existing
imports keep working."""

from src.scheduler.booking_sitemap.service import export_sitemap_ndjson

__all__ = ["export_sitemap_ndjson"]
