from src.app import db
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Dict, Any



class HotelListing(db.Model):
  __tablename__ = "hotel_listings"

  id = db.Column(db.Integer, primary_key=True)
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
    update_on_conflict: bool = False,
  ) -> int:
    """Insert many rows in a single transactional scope.

    - Uses PostgreSQL ON CONFLICT to handle duplicates on (hotel_url, origin).
    - If update_on_conflict=True, updates location/lastmod and touches updated_at.
    - Processes in chunks inside one transaction to limit memory.

    rows: list of dicts with keys: hotel_url, origin, location, lastmod
    returns: number of input rows attempted (not the number newly inserted)
    """
    if not rows:
      return 0

    base_stmt = pg_insert(cls.__table__)
    if update_on_conflict:
      stmt = base_stmt.on_conflict_do_update(
        index_elements=['hotel_url', 'origin'],
        set_={
          'location': base_stmt.excluded.location,
          'lastmod': base_stmt.excluded.lastmod,
          'updated_at': func.now(),
        }
      )
    else:
      stmt = base_stmt.on_conflict_do_nothing(
        index_elements=['hotel_url', 'origin']
      )

    def _chunks(seq, n):
      for i in range(0, len(seq), n):
        yield seq[i:i+n]

    total = 0
    try:
      for chunk in _chunks(rows, chunk_size):
        db.session.execute(stmt, chunk)
        total += len(chunk)
      db.session.commit()
    except Exception:
      db.session.rollback()
      raise

    return total
