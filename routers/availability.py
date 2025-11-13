from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from database import get_db
from models import Car, Booking, Airport
from schemas import AvailabilityCarOut, AvailabilityResponse

router = APIRouter(prefix="/availability", tags=["availability"])

@router.get("/", response_model=AvailabilityResponse)
def check_availability(
    airport_id: int = Query(..., description="Airport ID"),
    start_time: datetime = Query(..., description="Desired hire start time (UTC)"),
    end_time: datetime = Query(..., description="Desired hire end time (UTC)"),
    db: Session = Depends(get_db)
):
    """
    Returns all cars at the specified airport that are NOT booked
    during the given time window.
    """

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # --- Validate airport exists
    airport = db.query(Airport).filter(Airport.airports_id == airport_id, Airport.is_active == True).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found or inactive")

    # --- Step 1: Get all cars at this airport
    all_cars = db.query(Car).filter(
        Car.airport_id == airport_id,
        Car.status.in_(["active", "available"])
    ).all()

    if not all_cars:
        return {"available_cars": [], "total_available": 0, "airport": airport.name}

    # --- Step 2: Get all overlapping bookings for these cars
    overlapping = db.query(Booking.car_id).filter(
        Booking.car_id.in_([car.cars_id for car in all_cars]),
        Booking.status.in_(["active", "confirmed", "in_progress"]),
        and_(
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
    ).distinct().all()

    booked_car_ids = {r.car_id for r in overlapping}

    # --- Step 3: Filter available ones
    available = [car for car in all_cars if car.cars_id not in booked_car_ids]

    # --- Step 4: Return clean JSON
    return {
        "airport": airport.name,
        "total_available": len(available),
        "available_cars": [
            {
                "cars_id": car.cars_id,
                "registration": car.registration,
                "make_model": car.make_model,
                "price_hourly": float(car.price_hourly) if car.price_hourly else None,
                "keyfob_code": car.keyfob_code,
                "lockbox_ble_name": car.lockbox_ble_name,
                "status": car.status
            }
            for car in available
        ]
    }

