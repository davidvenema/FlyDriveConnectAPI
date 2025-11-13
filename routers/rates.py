from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Rate
from schemas import RateCreate, RateUpdate, RateOut

router = APIRouter(prefix="/rates", tags=["rates"])

@router.get("/", response_model=list[RateOut])
def list_rates(db: Session = Depends(get_db), active_only: bool = True, airports_id: int | None = None):
    q = db.query(Rate)
    if active_only:
        q = q.filter(Rate.is_active == True)
    if airports_id is not None:
        q = q.filter(Rate.airports_id == airports_id)
    return q.order_by(Rate.rate_name).all()

@router.post("/", response_model=RateOut)
def create_rate(payload: RateCreate, db: Session = Depends(get_db)):
    obj = Rate(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/{rates_id}", response_model=RateOut)
def update_rate(rates_id: int, payload: RateUpdate, db: Session = Depends(get_db)):
    obj = db.query(Rate).get(rates_id)
    if not obj:
        raise HTTPException(404, "Rate not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
