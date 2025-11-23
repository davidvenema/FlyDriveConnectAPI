from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import boto3
import os

from database import get_db
from security import get_current_member
from models import Member
from schemas import MemberUpdate, MemberOut

router = APIRouter(
    prefix="/members",
    tags=["members"],
)

# =====================================================
# AWS S3 CONFIG
# =====================================================

S3_BUCKET = "flydrive_userfiles"
REGION = "ap-southeast-2"

s3 = boto3.client("s3", region_name=REGION)


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


# =====================================================
# 3) GET /members/{id}/upload-presign  → get S3 URLs
# =====================================================
@router.get("/{members_id}/upload-presign")
def get_upload_presigned_urls(
    members_id: int,
    current_user: Member = Depends(get_current_member)
):

    if members_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    base = f"members/{members_id}"

    def presign(key_name: str):
        return s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": key_name,
                "ContentType": "image/jpeg"
            },
            ExpiresIn=3600,
        )

    front_key = f"{base}/licence_front.jpg"
    back_key = f"{base}/licence_back.jpg"

    return {
        "licence_front_url": presign(front_key),
        "licence_back_url": presign(back_key)
    }


# =====================================================
# 4) POST /members/{id}/complete-profile
# =====================================================
@router.post("/{members_id}/complete-profile")
def complete_profile(
    members_id: int,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_member)
):

    if members_id != current_user.members_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # Update member with provided profile info
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    # Move status to pending verification
    current_user.status = "pending_verification"

    db.commit()
    db.refresh(current_user)

    return {"status": "pending_verification"}


# =====================================================================
# 5) ADMIN / INTERNAL ENDPOINTS — PROTECT NOW, ROLE CHECK LATER
# =====================================================================

def require_admin(current_user: Member = Depends(get_current_member)):
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


# -----------------------------------------------------
# ADMIN: list pending verification
# -----------------------------------------------------
@router.get("/pending", response_model=list[MemberOut], dependencies=[Depends(require_admin)])
def admin_pending_members(db: Session = Depends(get_db)):
    return db.query(Member).filter(Member.status == "pending_verification").all()


# -----------------------------------------------------
# ADMIN: approve user
# -----------------------------------------------------
@router.post("/{members_id}/approve", dependencies=[Depends(require_admin)])
def admin_approve_member(members_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).get(members_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.status = "verified"
    db.commit()
    return {"message": "Member approved"}


# -----------------------------------------------------
# ADMIN: reject user
# -----------------------------------------------------
@router.post("/{members_id}/reject", dependencies=[Depends(require_admin)])
def admin_reject_member(members_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).get(members_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.status = "rejected"
    db.commit()
    return {"message": "Member rejected"}
