from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from database import get_db
from models import Booking, Car
from schemas import BookingCreate, BookingUpdate, BookingOut

router = APIRouter(prefix="/bookings", tags=["bookings"])

# --- List all bookings (unchanged)
@router.get("/", response_model=list[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    member_id: int | None = None,
    car_id: int | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None
):
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


# --- Create booking with overlap protection
@router.post("/", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    """
    Creates a booking if and only if no overlap exists for the same car.
    """

    # --- 1️⃣ Check that car exists
    car = db.query(Car).filter(Car.cars_id == payload.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # --- 2️⃣ Check for overlapping bookings
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

    # --- 3️⃣ Create new booking
    new_booking = Booking(**payload.model_dump(exclude_unset=True))
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


# --- Update booking (unchanged)
@router.put("/{bookings_id}", response_model=BookingOut)
def update_booking(bookings_id: int, payload: BookingUpdate, db: Session = Depends(get_db)):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


# --- Delete booking (optional)
@router.delete("/{bookings_id}")
def delete_booking(bookings_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).get(bookings_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    db.delete(booking)
    db.commit()
    return {"ok": True}
