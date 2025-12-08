import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from database import get_db
from security import get_current_member
from models import Booking, Member, Car
from schemas import (
    BookingCreate,
    BookingUpdate,
    BookingOut,
    BookingPhotoUpdate,
)

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    dependencies=[Depends(get_current_member)],  # All routes require JWT
)


# -------------------------------------------------------------------
# Utility: Merge JSON for before/after photos
# -------------------------------------------------------------------
def merge_photo_json(existing: str | None, angle: str, url: str) -> str:
    try:
        data = json.loads(existing) if existing else {}
    except Exception:
        data = {}

    data[angle] = url
    return json.dumps(data)


# ===================================================================
# 1. LIST BOOKINGS (authenticated)
# ===================================================================
@router.get("/", response_model=list[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    """
    Returns all bookings for the logged-in user,
    including nested car + airport info.
    """
    bookings = (
        db.query(Booking)
        .join(Booking.car)
        .join(Car.airport)
        .filter(Booking.member_id == current_user.members_id)
        .order_by(Booking.start_time.desc())
        .all()
    )

    return bookings

# ===================================================================
# 2. CREATE BOOKING (authenticated)
# ===================================================================
@router.post("/", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    """
    The Android app sends ONLY:
        - car_id
        - start_time
        - end_time

    Backend injects:
        - member_id = current_user.members_id
    """

    # Assign the correct member ID
    payload.member_id = current_user.members_id

    # ---- Car must exist ----
    car = db.query(Car).filter(Car.cars_id == payload.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # ---- Prevent overlapping bookings ----
    overlap = db.query(Booking).filter(
        Booking.car_id == payload.car_id,
        Booking.status.in_(["active", "confirmed", "in_progress"]),
        and_(
            Booking.start_time < payload.end_time,
            Booking.end_time > payload.start_time,
        ),
    ).first()

    if overlap:
        raise HTTPException(
            status_code=409,
            detail="This car is already booked during the selected period.",
        )

    # ---- Create booking ----
    new_booking = Booking(**payload.model_dump(exclude_unset=True))
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


# ===================================================================
# 3. UPDATE BOOKING (owner-only)
# ===================================================================
@router.put("/{bookings_id}", response_model=BookingOut)
def update_booking(
    bookings_id: int,
    payload: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only owner can update
    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


# ===================================================================
# 4. DELETE BOOKING (owner-only)
# ===================================================================
@router.delete("/{bookings_id}")
def delete_booking(
    bookings_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    db.delete(booking)
    db.commit()
    return {"status": "deleted", "booking_id": bookings_id}


# ===================================================================
# 5. UPLOAD (BEFORE/AFTER) PHOTOS TO A BOOKING
# ===================================================================
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

    # Only owner
    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    # Update JSON photo fields
    if payload.photo_type == "before":
        booking.photos_before_urls = merge_photo_json(
            booking.photos_before_urls, payload.angle, payload.url
        )

    elif payload.photo_type == "after":
        booking.photos_after_urls = merge_photo_json(
            booking.photos_after_urls, payload.angle, payload.url
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="photo_type must be 'before' or 'after'",
        )

    db.commit()
    db.refresh(booking)

    return {
        "status": "updated",
        "booking_id": booking_id,
        "photo_type": payload.photo_type,
        "angle": payload.angle,
        "url": payload.url,
    }

