from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Subscription
from schemas import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/", response_model=list[SubscriptionOut])
def list_subs(db: Session = Depends(get_db), member_id: int | None = None, status: str | None = None):
    q = db.query(Subscription)
    if member_id is not None:
        q = q.filter(Subscription.member_id == member_id)
    if status is not None:
        q = q.filter(Subscription.status == status)
    return q.order_by(Subscription.subscriptions_id).all()

@router.post("/", response_model=SubscriptionOut)
def create_sub(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    obj = Subscription(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/{subscriptions_id}", response_model=SubscriptionOut)
def update_sub(subscriptions_id: int, payload: SubscriptionUpdate, db: Session = Depends(get_db)):
    obj = db.query(Subscription).get(subscriptions_id)
    if not obj:
        raise HTTPException(404, "Subscription not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
