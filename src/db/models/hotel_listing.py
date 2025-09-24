import logging
import uuid
from typing import List, Dict, Any

from src.app import db
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert as pg_insert, UUID



log = logging.getLogger(__name__)


class HotelListing(db.Model):
  __tablename__ = "hotel_listings"

  id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  hotel_url = db.Column(db.Text, nullable=False)
  location = db.Column(db.Text)
  lastmod = db.Column(db.Date)
  origin = db.Column(db.String(255), nullable=False)

  # Use UTC timestamps managed by DB defaults
  created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

  __table_args__ = (
    # Prevent duplicates for the same origin
    UniqueConstraint('hotel_url', 'origin', name='uq_hotel_url_origin'),
    # Fast lookups by location alone
    Index('ix_hotel_listings_location', 'location'),
    # Composite index supports queries by hotel_url alone (leading col)
    # and combined filters on (hotel_url, location)
    Index('ix_hotel_listings_hotel_url_location', 'hotel_url', 'location'),
  )

  def __init__(self, hotel_url, location, lastmod, origin):
    self.hotel_url = hotel_url
    self.location = location
    self.lastmod = lastmod
    self.origin = origin

  def add(self):
    db.session.add(self)
    db.session.commit()

  @classmethod
  def bulk_upsert(
    cls,
    rows: List[Dict[str, Any]],
    *,
    chunk_size: int = 1000,
  ) -> int:
    """Insert many rows in a single transactional scope.

    - Uses PostgreSQL ON CONFLICT DO NOTHING to avoid duplicates on (hotel_url, origin).
    - Processes in chunks to limit memory usage.

    rows: list of dicts with keys: hotel_url, origin, location, lastmod
    returns: number of rows inserted (duplicates skipped)
    """
    if not rows:
      return 0

    base_stmt = pg_insert(cls.__table__)
    stmt = base_stmt.on_conflict_do_nothing(
      index_elements=['hotel_url', 'origin']
    )

    def _chunks(seq, n):
      for i in range(0, len(seq), n):
        yield seq[i:i+n]

    attempted = 0
    inserted = 0
    try:
      for chunk in _chunks(rows, chunk_size):
        result = db.session.execute(stmt, chunk)
        chunk_count = len(chunk)
        attempted += chunk_count
        # rowcount reflects number of rows actually inserted (duplicates -> 0)
        inserted += result.rowcount or 0
      db.session.commit()
    except Exception:
      db.session.rollback()
      raise

    skipped = attempted - inserted
    if skipped:
      log.info(
        "hotel_listings bulk_upsert skipped %s duplicate rows (attempted=%s, inserted=%s)",
        skipped,
        attempted,
        inserted,
      )
    return inserted
