from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_member
from models import Member
from schemas import MemberUpdate, MemberOut

router = APIRouter(
    prefix="/members",
    tags=["members"],
)


# =====================================================
# 1) GET /members/me  → authenticated member profile
# =====================================================
@router.get("/me", response_model=MemberOut)
def get_my_profile(
    current_user: Member = Depends(get_current_member),
):
    return current_user


# =====================================================
# 2) PUT /members/me  → update own profile
# =====================================================
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



# =====================================================================
# 3) ADMIN / INTERNAL ENDPOINTS — PROTECT NOW, ROLE CHECK LATER
# =====================================================================

def require_admin(current_user: Member = Depends(get_current_member)):
    """
    Temporary admin check.
    For now: nobody is admin unless you manually modify the DB.
    Later we'll add Member.is_admin column.
    """
    if getattr(current_user, "platform", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


# -----------------------------------------------------
# ADMIN: list all members
# -----------------------------------------------------
@router.get("/", response_model=list[MemberOut], dependencies=[Depends(require_admin)])
def admin_list_members(db: Session = Depends(get_db)):
    return db.query(Member).order_by(Member.members_id).all()


# -----------------------------------------------------
# ADMIN: get a specific member
# -----------------------------------------------------
@router.get("/{members_id}", response_model=MemberOut, dependencies=[Depends(require_admin)])
def admin_get_member(members_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).get(members_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member
