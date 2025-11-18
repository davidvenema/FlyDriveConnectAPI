from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from database import get_db
from security import get_current_member_optional  # NEW (optional auth)
from models import Car, Booking, Airport, SearchLog
from schemas import AvailabilityCarOut, AvailabilityResponse

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("/", response_model=AvailabilityResponse)
def check_availability(
    airport_id: int = Query(..., description="Airport ID"),
    start_time: datetime = Query(..., description="Desired hire start time (UTC)"),
    end_time: datetime = Query(..., description="Desired hire end time (UTC)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_member_optional),   # NEW: optional login
):
    """
    Returns cars NOT booked in this window and automatically logs the search.
    """

    # -------------------------------------
    # 1. Validate airport exists
    # -------------------------------------
    airport = db.query(Airport).filter(
        Airport.airports_id == airport_id,
        Airport.is_active == True
    ).first()

    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found or inactive")

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # -------------------------------------
    # 2. Fetch all cars at the airport
    # -------------------------------------
    all_cars = db.query(Car).filter(
        Car.airport_id == airport_id,
        Car.status.in_(["active", "available"])
    ).all()

    # -------------------------------------
    # 3. Find overlapping bookings
    # -------------------------------------
    overlapping = db.query(Booking.car_id).filter(
        Booking.car_id.in_([c.cars_id for c in all_cars]),
        Booking.status.in_(["active", "confirmed", "in_progress"]),
        and_(Booking.start_time < end_time, Booking.end_time > start_time)
    ).distinct().all()

    booked_ids = {row.car_id for row in overlapping}
    available = [c for c in all_cars if c.cars_id not in booked_ids]

    # -------------------------------------
    # 4. AUTO-LOG THE SEARCH (SECURE)
    # -------------------------------------
    log = SearchLog(
        member_id=getattr(current_user, "members_id", None),  # None if anonymous
        airport_id=airport_id,
        search_date=start_time.date(),
        search_time=datetime.utcnow(),
        desired_start=start_time,
        desired_end=end_time
    )
    db.add(log)
    db.commit()

    # -------------------------------------
    # 5. Return clean response
    # -------------------------------------
    return {
        "airport": airport.name,
        "total_available": len(available),
        "available_cars": [
            {
                "cars_id": c.cars_id,
                "registration": c.registration,
                "make_model": c.make_model,
                "price_hourly": float(c.price_hourly) if c.price_hourly else None,
                "keyfob_code": c.keyfob_code,
                "lockbox_ble_name": c.lockbox_ble_name,
                "status": c.status
            }
            for c in available
        ]
    }
