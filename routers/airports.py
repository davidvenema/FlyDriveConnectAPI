from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Airport
from schemas import AirportCreate, AirportUpdate, AirportOut

router = APIRouter(prefix="/airports", tags=["airports"])

@router.get("/", response_model=list[AirportOut])
def list_airports(db: Session = Depends(get_db), active_only: bool = True):
    q = db.query(Airport)
    if active_only:
        q = q.filter(Airport.is_active == True)
    return q.order_by(Airport.name).all()

@router.get("/{airport_id}", response_model=AirportOut)
def get_airport(airport_id: int, db: Session = Depends(get_db)):
    obj = db.query(Airport).get(airport_id)
    if not obj:
        raise HTTPException(404, "Airport not found")
    return obj

@router.post("/", response_model=AirportOut)
def create_airport(payload: AirportCreate, db: Session = Depends(get_db)):
    obj = Airport(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/{airport_id}", response_model=AirportOut)
def update_airport(airport_id: int, payload: AirportUpdate, db: Session = Depends(get_db)):
    obj = db.query(Airport).get(airport_id)
    if not obj:
        raise HTTPException(404, "Airport not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{airport_id}")
def delete_airport(airport_id: int, db: Session = Depends(get_db)):
    obj = db.query(Airport).get(airport_id)
    if not obj:
        raise HTTPException(404, "Airport not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}
