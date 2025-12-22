from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Text,
    Boolean,
    Date,
    TIMESTAMP,
    ForeignKey,
)
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
    created_at = Column(TIMESTAMP(timezone=True))

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
    created_at = Column(TIMESTAMP(timezone=True))

    # Image fields
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
    renewal_date = Column(TIMESTAMP(timezone=True))
    platform = Column(String)
    created_at = Column(TIMESTAMP(timezone=True))
    status = Column(String, default="pending_verification")

    licence_front_url = Column(Text, nullable=True)
    licence_back_url = Column(Text, nullable=True)
    selfie_url = Column(Text, nullable=True)
    licence_number = Column(String, nullable=True)
    licence_expiry = Column(Date, nullable=True)

    bookings = relationship("Booking", back_populates="member")
    subscriptions = relationship("Subscription", back_populates="member")


class Booking(Base):
    __tablename__ = "bookings"

    bookings_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"))
    car_id = Column(Integer, ForeignKey("cars.cars_id"))

    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    status = Column(String)

    photos_before_urls = Column(Text)
    photos_after_urls = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True))
    hire_started_at = Column(TIMESTAMP(timezone=True))
    keys_retrieved_at = Column(TIMESTAMP(timezone=True))

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

    created_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))

    airport = relationship("Airport", back_populates="rates")


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscriptions_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"))
    platform = Column(String)
    purchase_token = Column(Text)
    status = Column(String)

    renewal_date = Column(TIMESTAMP(timezone=True))
    last_checked = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True))

    member = relationship("Member", back_populates="subscriptions")


class SearchLog(Base):
    __tablename__ = "search_logs"

    search_logs_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.members_id"), nullable=True)
    airport_id = Column(Integer, ForeignKey("airports.airports_id"), nullable=True)

    search_date = Column(Date)
    search_time = Column(TIMESTAMP(timezone=True))
    desired_start = Column(TIMESTAMP(timezone=True))
    desired_end = Column(TIMESTAMP(timezone=True))
