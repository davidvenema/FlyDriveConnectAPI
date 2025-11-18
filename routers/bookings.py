import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from database import get_db
from security import get_current_member     #  AUTH HERE
from models import Booking, Member, Car
from schemas import BookingCreate, BookingUpdate, BookingOut, BookingPhotoUpdate

# Protect ALL booking routes — only authenticated users can access
router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    dependencies=[Depends(get_current_member)],   #  JWT ENFORCED
)

# If you ever want some routes to be public, remove this ^ and put Depends on individual routes.

def merge_photo_json(existing: str | None, angle: str, url: str) -> str:
    """Safely merge/update JSON stored in DB text fields."""
    try:
        data = json.loads(existing) if existing else {}
    except:
        data = {}

    data[angle] = url
    return json.dumps(data)

# ======================================================
# 1️ LIST BOOKINGS (optionally admin-only)
# ======================================================
@router.get("/", response_model=list[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),  #  You now know *who* is logged in
    member_id: int | None = None,
    car_id: int | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
):
    # NOTE: If you want members to only see THEIR bookings, uncomment this:
    #
    # member_id = current_user.members_id
    #

    q = db.query(Booking)
    if member_id is not None:
        q = q.filter(Booking.member_id == member_id)
    if car_id is not None:
        q = q.filter(Booking.car_id == car_id)
    if from_time is not None:
        q = q.filter(Booking.start_time >= from_time)
    if to_time is not None:
        q = q.filter(Booking.end_time <= to_time)

    return q.order_by(Booking.start_time.desc()).all()


# ======================================================
# 2️ CREATE BOOKING (JWT REQUIRED)
# ======================================================
@router.post("/", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),   #  REQUIRE USER LOGGED IN
):

    # --- Force booking to ALWAYS belong to logged-in user ---
    payload.member_id = current_user.members_id   #  SECURITY FIX

    # --- 1. Car must exist ---
    car = db.query(Car).filter(Car.cars_id == payload.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # --- 2. Prevent overlapping bookings ---
    overlap = db.query(Booking).filter(
        Booking.car_id == payload.car_id,
        Booking.status.in_(["active", "confirmed", "in_progress"]),
        and_(
            Booking.start_time < payload.end_time,
            Booking.end_time > payload.start_time
        )
    ).first()

    if overlap:
        raise HTTPException(
            status_code=409,
            detail="This car is already booked during the selected period."
        )

    # --- 3. Create the booking ---
    new_booking = Booking(**payload.model_dump(exclude_unset=True))
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


# ======================================================
# 3️ UPDATE BOOKING
# ======================================================
@router.put("/{bookings_id}", response_model=BookingOut)
def update_booking(
    bookings_id: int,
    payload: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),  #  REQUIRED
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # --- Users can only update THEIR OWN bookings ---
    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


# ======================================================
# 4️ DELETE BOOKING
# ======================================================
@router.delete("/{bookings_id}")
def delete_booking(
    bookings_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),  #  REQUIRED
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # --- Ensure user owns it ---
    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    db.delete(booking)
    db.commit()
    return {"ok": True}

# ======================================================
# 5️ UPDATE BOOKING PHOTO (before/after)
# ======================================================
@router.post("/{booking_id}/photo")
def update_booking_photo(
    booking_id: int,
    payload: BookingPhotoUpdate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # --- Ensure user owns the booking ---
    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    # --- Insert/Update photo in JSON field ---
    if payload.photo_type == "before":
        booking.photos_before_urls = merge_photo_json(
            booking.photos_before_urls,
            payload.angle,
            payload.url
        )
    elif payload.photo_type == "after":
        booking.photos_after_urls = merge_photo_json(
            booking.photos_after_urls,
            payload.angle,
            payload.url
        )
    else:
        raise HTTPException(400, "photo_type must be 'before' or 'after'")

    db.commit()
    db.refresh(booking)

    return {
        "status": "updated",
        "booking_id": booking_id,
        "photo_type": payload.photo_type,
        "angle": payload.angle,
        "url": payload.url
    }
