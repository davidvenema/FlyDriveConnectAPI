import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Member
from schemas import SocialLoginRequest, AuthResponse, MemberOut
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_WEB_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")


# ---------------------------------------------------------
# Validate Google ID Token
# ---------------------------------------------------------
def verify_google_id_token(id_token: str):
    try:
        resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return None

        data = resp.json()

        # Must have email
        if "email" not in data:
            return None

        # Ensure audience matches our Web Client ID
        if GOOGLE_WEB_CLIENT_ID and data.get("aud") != GOOGLE_WEB_CLIENT_ID:
            return None

        return data

    except Exception as e:
        print("verify_google_id_token ERROR:", e)
        return None


# ---------------------------------------------------------
# POST /auth/google
# ---------------------------------------------------------
@router.post("/google", response_model=AuthResponse)
def login_with_google(
    payload: SocialLoginRequest,
    db: Session = Depends(get_db)
):

    if payload.provider.lower() != "google":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Verify ID token with Google
    data = verify_google_id_token(payload.id_token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = data["email"].lower()
    name = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()

    # Look for existing member
    member = db.query(Member).filter(Member.email == email).first()

    # If no account -> create as *new_user*
    if not member:
        member = Member(
            email=email,
            name=name,
            platform="google",
            status="new_user",      # ← IMPORTANT
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

    # -----------------------------
    # Return based on status
    # -----------------------------
    # 1. Rejected → no token
    if member.status == "rejected":
        return AuthResponse(
            status="rejected",
            access_token=None,
            token_type=None,
            member=MemberOut.model_validate(member)
        )

    # 2. Pending verification → no token
    if member.status == "pending_verification":
        return AuthResponse(
            status="pending_verification",
            access_token=None,
            token_type=None,
            member=MemberOut.model_validate(member)
        )

    # 3. new_user → they MUST complete profile
    if member.status == "new_user":
        token = create_access_token({"sub": member.email})
        return AuthResponse(
            status="new_user",
            access_token=token,
            token_type="bearer",
            member=MemberOut.model_validate(member)
        )

    # 4. verified → full access
    if member.status == "verified":
        token = create_access_token({"sub": member.email})
        return AuthResponse(
            status="verified",
            access_token=token,
            token_type="bearer",
            member=MemberOut.model_validate(member)
        )

    # Should never reach here
    raise HTTPException(500, "Unknown member status")
