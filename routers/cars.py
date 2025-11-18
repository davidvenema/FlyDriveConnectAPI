from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_member
from models import Car, Airport
from schemas import CarCreate, CarUpdate, CarOut

router = APIRouter(prefix="/cars", tags=["cars"])

# ===========================================================
# Helper: require admin
# ===========================================================
def require_admin(current_user = Depends(get_current_member)):
    # Later replace with user.is_admin Boolean
    if getattr(current_user, "platform", "") != "admin":
        raise HTTPException(403, "Admin access required.")
    return current_user

# ===========================================================
# PUBLIC: List cars
# ===========================================================
@router.get("/", response_model=list[CarOut])
def list_cars(
    db: Session = Depends(get_db),
    airport_id: int | None = None,
    status: str | None = None,
):
    q = db.query(Car)
    if airport_id is not None:
        q = q.filter(Car.airport_id == airport_id)
    if status is not None:
        q = q.filter(Car.status == status)

    return q.order_by(Car.registration).all()

# ===========================================================
# ADMIN: Create car
# ===========================================================
@router.post("/", response_model=CarOut, dependencies=[Depends(require_admin)])
def create_car(
    payload: CarCreate,
    db: Session = Depends(get_db),
):
    obj = Car(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ===========================================================
# ADMIN: Update car
# ===========================================================
@router.put("/{cars_id}", response_model=CarOut, dependencies=[Depends(require_admin)])
def update_car(
    cars_id: int,
    payload: CarUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(Car).get(cars_id)
    if not obj:
        raise HTTPException(404, "Car not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj

# ===========================================================
# ADMIN: Delete car
# ===========================================================
@router.delete("/{cars_id}", dependencies=[Depends(require_admin)])
def delete_car(
    cars_id: int,
    db: Session = Depends(get_db),
):
    obj = db.query(Car).get(cars_id)
    if not obj:
        raise HTTPException(404, "Car not found")

    db.delete(obj)
    db.commit()

    return {"ok": True}
