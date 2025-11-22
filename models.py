from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, Date, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Airport(Base):
    __tablename__ = "airports"
    airports_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    icao_code = Column(String)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    parking_description = Column(Text)
    is_active = Column(Boolean)
    created_at = Column(TIMESTAMP)

    cars = relationship("Car", back_populates="airport")
    rates = relationship("Rate", back_populates="airport")

class Car(Base):
    __tablename__ = "cars"
    cars_id = Column(Integer, primary_key=True, index=True)
    registration = Column(String)
    make_model = Column(String)
    airport_id = Column(Integer, ForeignKey("airports.airports_id"))
    status = Column(String)
    price_hourly = Column(Numeric)
    lockbox_ble_name = Column(String)
    lockbox_serial = Column(String)
    keyfob_code = Column(String)
    created_at = Column(TIMESTAMP)
    # NEW IMAGE FIELDS
    image_url = Column(Text)
    carleft_url = Column(Text)
    carright_url = Column(Text)
    carback_url = Column(Text)
    carfront_url = Column(Text)
    cardash_url = Column(Text)
    
    airport = relationship("Airport", back_populates="cars")
    bookings = relationship("Booking", back_populates="car")

class Member(Base):
    __tablename__ = "members"
    members_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    dob = Column(Date)
    address = Column(Text)
    renewal_date = Column(TIMESTAMP)
    platform = Column(String)
    created_at = Column(TIMESTAMP)
    status = Column(String, default="pending_verification")     # NEW
    licence_front_url = Column(Text, nullable=True)             # NEW
    licence_back_url = Column(Text, nullable=True)              # NEW
    selfie_url = Column(Text, nullable=True)                    # NEW

    bookings = relationship("Booking", back_populates="member")
    subscriptions = relationship("Subscription", back_populates="member")

class Booking(Base):
    __tablename__ = "bookings"
    bookings_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"))
    car_id = Column(Integer, ForeignKey("cars.cars_id"))
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    status = Column(String)
    photos_before_urls = Column(Text)   # store JSON as text or switch to SQLAlchemy JSON
    photos_after_urls = Column(Text)
    created_at = Column(TIMESTAMP)

    member = relationship("Member", back_populates="bookings")
    car = relationship("Car", back_populates="bookings")

class Rate(Base):
    __tablename__ = "rates"
    rates_id = Column(Integer, primary_key=True, index=True)
    airports_id = Column(Integer, ForeignKey("airports.airports_id"))
    rate_name = Column(String)
    hourly_rate = Column(Numeric)
    discount_threshold_hours = Column(Integer)
    discount_percent = Column(Numeric)
    gst_percent = Column(Numeric)
    is_gst_inclusive = Column(Boolean)
    active_from = Column(Date)
    active_to = Column(Date)
    is_active = Column(Boolean)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    airport = relationship("Airport", back_populates="rates")

class Subscription(Base):
    __tablename__ = "subscriptions"
    subscriptions_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"))
    platform = Column(String)
    purchase_token = Column(Text)
    status = Column(String)
    renewal_date = Column(TIMESTAMP)
    last_checked = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    member = relationship("Member", back_populates="subscriptions")

class SearchLog(Base):
    __tablename__ = "search_logs"
    search_logs_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"), nullable=True)
    airport_id = Column(Integer, ForeignKey("airports.airports_id"), nullable=True)
    search_date = Column(Date)
    search_time = Column(TIMESTAMP)
    desired_start = Column(TIMESTAMP)
    desired_end = Column(TIMESTAMP)

    # Relationships optional here; mostly append-only log


