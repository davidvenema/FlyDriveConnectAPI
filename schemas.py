from pydantic import BaseModel
from typing import Literal, Dict, Optional, List, Any
from datetime import datetime, date

# Airports
class AirportBase(BaseModel):
    name: Optional[str] = None
    icao_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parking_description: Optional[str] = None
    is_active: Optional[bool] = True

class AirportCreate(AirportBase):
    name: str

class AirportUpdate(AirportBase):
    pass

class AirportOut(AirportBase):
    airports_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Cars
class CarBase(BaseModel):
    registration: Optional[str] = None
    make_model: Optional[str] = None
    airport_id: Optional[int] = None
    status: Optional[str] = None
    price_hourly: Optional[float] = None
    lockbox_ble_name: Optional[str] = None
    lockbox_serial: Optional[str] = None
    keyfob_code: Optional[str] = None
    # IMAGE FIELDS
    image_url: Optional[str] = None
    carleft_url: Optional[str] = None
    carright_url: Optional[str] = None
    carback_url: Optional[str] = None
    carfront_url: Optional[str] = None
    cardash_url: Optional[str] = None


class CarCreate(CarBase):
    registration: str

class CarUpdate(CarBase):
    pass

class CarOut(CarBase):
    cars_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Members
class MemberBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    renewal_date: Optional[datetime] = None
    platform: Optional[str] = None
    # NEW
    status: Optional[str] = None
    licence_front_url: Optional[str] = None
    licence_back_url: Optional[str] = None
    selfie_url: Optional[str] = None
    
class MemberCreate(MemberBase):
    email: str

class MemberUpdate(MemberBase):
    pass

class MemberOut(MemberBase):
    members_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Bookings
class BookingBase(BaseModel):
    member_id: int
    car_id: int
    start_time: datetime
    end_time: datetime
    status: Optional[str] = "pending"
    photos_before_urls: Optional[Any] = None
    photos_after_urls: Optional[Any] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    photos_before_urls: Optional[Any] = None
    photos_after_urls: Optional[Any] = None

class BookingOut(BookingBase):
    bookings_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Rates
class RateBase(BaseModel):
    airports_id: Optional[int] = None
    rate_name: Optional[str] = None
    hourly_rate: Optional[float] = None
    discount_threshold_hours: Optional[int] = None
    discount_percent: Optional[float] = None
    gst_percent: Optional[float] = None
    is_gst_inclusive: Optional[bool] = None
    active_from: Optional[date] = None
    active_to: Optional[date] = None
    is_active: Optional[bool] = True

class RateCreate(RateBase):
    rate_name: str
    hourly_rate: float

class RateUpdate(RateBase):
    pass

class RateOut(RateBase):
    rates_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Subscriptions
class SubscriptionBase(BaseModel):
    member_id: int
    platform: Optional[str] = None
    purchase_token: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[datetime] = None
    last_checked: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    platform: Optional[str] = None
    purchase_token: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[datetime] = None
    last_checked: Optional[datetime] = None

class SubscriptionOut(SubscriptionBase):
    subscriptions_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Search logs
class SearchLogBase(BaseModel):
    member_id: Optional[int] = None
    airport_id: Optional[int] = None
    search_date: Optional[date] = None
    search_time: Optional[datetime] = None
    desired_start: Optional[datetime] = None
    desired_end: Optional[datetime] = None

class SearchLogCreate(SearchLogBase):
    pass

class SearchLogOut(SearchLogBase):
    search_logs_id: int
    class Config:
        from_attributes = True

# ----------------------------
# Availability Schemas
# ----------------------------

class AvailabilityCarOut(BaseModel):
    cars_id: int
    registration: str
    make_model: Optional[str] = None
    price_hourly: Optional[float] = None
    keyfob_code: Optional[str] = None
    lockbox_ble_name: Optional[str] = None
    status: Optional[str] = None
    # image fields
    image_url: Optional[str] = None
    carleft_url: Optional[str] = None
    carright_url: Optional[str] = None
    carback_url: Optional[str] = None
    carfront_url: Optional[str] = None
    cardash_url: Optional[str] = None

    class Config:
        from_attributes = True


class AvailabilityResponse(BaseModel):
    airport: str
    total_available: int
    available_cars: List[AvailabilityCarOut]

# ----------------------------
# Auth schemas (social login)
# ----------------------------

class SocialLoginRequest(BaseModel):
    provider: str  # e.g. "google" (Apple later if you like)
    id_token: str  # ID token returned by Google/Apple on the device

class BookingPhotoUpdate(BaseModel):
    photo_type: str          # "before" or "after"
    angle: str               # "left", "right", "front", etc.
    url: str                 # public URL returned from /upload/presign

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

