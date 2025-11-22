import os
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Member
from schemas import SocialLoginRequest, AuthResponse
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_WEB_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")


def verify_google_id_token(id_token: str):
    try:
        resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return None

        data = resp.json()

        # must contain email
        if "email" not in data:
            return None

        # enforce audience check (only if env var provided)
        if GOOGLE_WEB_CLIENT_ID and data.get("aud") != GOOGLE_WEB_CLIENT_ID:
            return None

        return data

    except Exception:
        return None


@router.post("/google", response_model=AuthResponse)
def login_with_google(
    payload: SocialLoginRequest,
    db: Session = Depends(get_db)
):

    if payload.provider.lower() != "google":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Verify Google token
    data = verify_google_id_token(payload.id_token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = data["email"].lower()
    name = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()

    # Find member
    member = db.query(Member).filter(Member.email == email).first()

    # Create new member
    if not member:
        member = Member(
            email=email,
            name=name,
            platform="google",
            status="pending_verification",
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    # Update name/platform if changed
    dirty = False
    if name and member.name != name:
        member.name = name
        dirty = True
    if member.platform != "google":
        member.platform = "google"
        dirty = True

    if dirty:
        db.commit()
        db.refresh(member)

    # Handle states
    if member.status == "rejected":
        return AuthResponse(
            status="rejected",
            access_token="",
            token_type=""
        )

    if member.status == "pending_verification":
        return AuthResponse(
            status="pending_verification",
            access_token="",
            token_type=""
        )

    # VERIFIED (normal)
    token = create_access_token({"sub": member.email})

    return AuthResponse(
        status="verified",
        access_token=token,
        token_type="bearer"
    )
