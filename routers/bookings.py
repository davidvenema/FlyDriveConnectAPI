import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta, timezone

from utils.email_utils import send_booking_confirmation_email
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
    dependencies=[Depends(get_current_member)],
)

# ===================================================================
# 1. LIST BOOKINGS
# ===================================================================
@router.get("/", response_model=list[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
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
# 2. CREATE BOOKING
# ===================================================================
@router.post("/", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    payload.member_id = current_user.members_id

    # ---- Defensive: ensure timezone-aware UTC datetimes ----
    if payload.start_time.tzinfo is None or payload.end_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="start_time and end_time must include timezone information (UTC)",
        )

    payload.start_time = payload.start_time.astimezone(timezone.utc)
    payload.end_time = payload.end_time.astimezone(timezone.utc)

    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    car = db.query(Car).filter(Car.cars_id == payload.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

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

    new_booking = Booking(**payload.model_dump(exclude_unset=True))
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # ---- Fire-and-forget email ----
    try:
        send_booking_confirmation_email(
            member=current_user,
            booking=new_booking,
            car=new_booking.car,
            airport=new_booking.car.airport,
        )
    except Exception as e:
        print(f"Booking email failed: {e!r}")

    return new_booking

# ===================================================================
# 3. UPDATE BOOKING
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

    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking

# ===================================================================
# 4. DELETE BOOKING
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
# 5. START HIRE
# ===================================================================
@router.put("/{bookings_id}/start", response_model=BookingOut)
def start_hire(
    bookings_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Cannot start hire")

    booking.status = "in_progress"
    booking.hire_started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(booking)
    return booking

# ===================================================================
# 5.5 COMPLETE KEY RETRIEVAL (Physical Confirmation)
# ===================================================================
@router.put("/{bookings_id}/complete-keys", response_model=BookingOut)
def complete_keys(
    bookings_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    # Set the key retrieval timestamp - the "Physical Truth" milestone
    booking.keys_retrieved_at = datetime.now(timezone.utc)
    
    # Ensure status is definitely in_progress if it wasn't already
    booking.status = "in_progress"

    db.commit()
    db.refresh(booking)
    return booking

# ===================================================================
# 6. GET ACTIVE BOOKING
# ===================================================================
@router.get("/active", response_model=BookingOut | None)
def get_active_booking(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    now = datetime.now(timezone.utc)

    expired = (
        db.query(Booking)
        .filter(
            Booking.member_id == current_user.members_id,
            Booking.status == "in_progress",
            Booking.end_time < now,
        )
        .update({Booking.status: "expired"}, synchronize_session=False)
    )

    if expired:
        db.commit()

    booking = (
        db.query(Booking)
        .join(Booking.car)
        .join(Car.airport)
        .filter(
            Booking.member_id == current_user.members_id,
            Booking.status == "in_progress",
            Booking.start_time <= now,
            Booking.end_time >= now,
        )
        .order_by(Booking.start_time.desc())
        .first()
    )

    return booking

# ===================================================================
# 6.5 GET BOOKING BY ID
# ===================================================================
@router.get("/{bookings_id}", response_model=BookingOut)
def get_booking_by_id(
    bookings_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    booking = (
        db.query(Booking)
        .join(Booking.car)
        .join(Car.airport)
        .filter(
            Booking.bookings_id == bookings_id,
            Booking.member_id == current_user.members_id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking

# ===================================================================
# 7. CHECK PRECEDING BOOKING
# ===================================================================
@router.get("/is-preceding-booking")
def is_preceding_booking(
    car_id: int,
    start_time: datetime,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    if start_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="start_time must include timezone information (UTC)",
        )

    start_time = start_time.astimezone(timezone.utc)
    buffer = timedelta(minutes=30)

    exists = (
        db.query(Booking)
        .filter(
            Booking.car_id == car_id,
            Booking.end_time <= start_time,
            Booking.end_time >= start_time - buffer,
            Booking.status.in_(["confirmed", "in_progress"]),
        )
        .order_by(desc(Booking.end_time))
        .first()
        is not None
    )

    return {"is_preceding_booking": exists}

# ===================================================================
# 8. UPLOAD BOOKING PHOTOS
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

    if booking.member_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not your booking")

    column_name = f"photourl_{payload.phase}_{payload.angle}"

    if not hasattr(Booking, column_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid photo slot: {column_name}",
        )

    setattr(booking, column_name, payload.url)

    db.commit()
    db.refresh(booking)

    return {
        "status": "updated",
        "booking_id": booking_id,
        "slot": column_name,
        "url": payload.url,
    }


