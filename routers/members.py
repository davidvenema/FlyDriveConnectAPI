from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from security import get_current_member
from models import Member
from schemas import MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["members"])


# -----------------------------------------
# GET /members/me  → return your own profile
# -----------------------------------------
@router.get("/me", response_model=MemberOut)
def get_my_profile(
    current_user: Member = Depends(get_current_member),
):
    return current_user


# -----------------------------------------
# PUT /members/me  → update your own profile
# -----------------------------------------
@router.put("/me", response_model=MemberOut)
def update_my_profile(
    payload: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


# ==================================================
# ADMIN / INTERNAL ENDPOINTS (optional, for later)
# ==================================================

# Only for internal admin use (currently locked down)
@router.get("/", response_model=list[MemberOut])
def admin_list_members(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    # optional: enforce admin role later
    return db.query(Member).order_by(Member.members_id).all()


@router.get("/{members_id}", response_model=MemberOut)
def admin_get_member(
    members_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member),
):
    member = db.query(Member).get(members_id)
    if not member:
        raise HTTPException(404, "Member not found")

    # Only allow viewing yourself (or admin later)
    if member.members_id != current_user.members_id:
        raise HTTPException(403, "Not permitted")

    return member
