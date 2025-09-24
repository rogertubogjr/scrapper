from src.app import db
from sqlalchemy import ForeignKey
from datetime import datetime
import pytz



class HotelListing(db.Model):
  __tablename__ = "hotel_listings"
  id = db.Column(db.Integer, primary_key=True)
  hotel_url = db.Column(db.Text)
  location = db.Column(db.Text)
  lastmod = db.Column(db.Date)
  origin = db.Column(db.String(255))

  createdAt = db.Column(db.DateTime(timezone='Asia/Manila'), default=datetime.now(pytz.timezone('Asia/Manila')))
  updatedAt = db.Column(db.DateTime(timezone='Asia/Manila'), onupdate = datetime.now(pytz.timezone('Asia/Manila')))

  def __init__(self, hotel_url, location, lastmod, origin):
    self.hotel_url = hotel_url
    self.location = location
    self.lastmod = lastmod
    self.origin = origin
    self.createdAt = datetime.now(pytz.timezone('Asia/Manila'))

  def add(self):
    db.session.add(self)
    db.session.commit()