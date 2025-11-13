from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Member
from schemas import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["members"])

@router.get("/", response_model=list[MemberOut])
def list_members(db: Session = Depends(get_db), email: str | None = None):
    q = db.query(Member)
    if email:
        q = q.filter(Member.email == email)
    return q.order_by(Member.members_id).all()

@router.post("/", response_model=MemberOut)
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    obj = Member(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/{members_id}", response_model=MemberOut)
def update_member(members_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    obj = db.query(Member).get(members_id)
    if not obj:
        raise HTTPException(404, "Member not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
