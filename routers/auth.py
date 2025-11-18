import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Member
from schemas import SocialLoginRequest, Token
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


# ------------------------------------------------------
# GOOGLE TOKEN VERIFICATION
# ------------------------------------------------------
def verify_google_id_token(id_token: str) -> dict | None:
    """
    Verifies a Google ID token using Google's tokeninfo endpoint.
    This automatically checks the signature and expiry.

    IMPORTANT:
      In production, verify 'aud' against your Android/iOS client IDs.
    """
    try:
        resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return None
        data = resp.json()

        # Must contain an email
        if "email" not in data:
            return None

        # Optional: enforce audience check later
        # if data.get("aud") != YOUR_ANDROID_CLIENT_ID:
        #     return None

        return data

    except Exception:
        return None


# ------------------------------------------------------
# LOGIN (GOOGLE or APPLE — Apple disabled for now)
# ------------------------------------------------------
@router.post("/login", response_model=Token)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    provider = payload.provider.lower()

    # ---------------- GOOGLE ----------------
    if provider == "google":
        data = verify_google_id_token(payload.id_token)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token",
            )

    # ---------------- APPLE (NOT YET IMPLEMENTED) ----------------
    elif provider == "apple":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple Sign-In not implemented yet",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    email = data.get("email")
    name = data.get("name") or data.get("given_name") or ""

    # ---------------- FIND OR CREATE MEMBER ----------------
    member = db.query(Member).filter(Member.email == email).first()

    if not member:
        member = Member(
            name=name,
            email=email,
            platform=provider,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    # ---------------- CREATE 24-HOUR JWT ----------------
    access_token = create_access_token(data={"sub": member.email})

    return Token(access_token=access_token, token_type="bearer")
