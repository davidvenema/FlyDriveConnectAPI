import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Member
from schemas import SocialLoginRequest, Token
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_google_id_token(id_token: str) -> dict | None:
    """
    Verifies a Google ID token using Google's tokeninfo endpoint.
    In production you may also want to validate 'aud' against your
    Android client ID.
    """
    resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
    if resp.status_code != 200:
        return None
    data = resp.json()
    if "email" not in data:
        return None
    return data


@router.post("/login", response_model=Token)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    provider = payload.provider.lower()

    if provider == "google":
        data = verify_google_id_token(payload.id_token)
    elif provider == "apple":
        # TODO: implement real Apple token verification later
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple Sign-In not implemented on backend yet.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID token",
        )

    email = data.get("email")
    name = data.get("name") or data.get("given_name") or ""

    # --- Find or create Member ---
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

    # --- Create 24-hour JWT with subject=email ---
    access_token = create_access_token(data={"sub": member.email})

    return Token(access_token=access_token, token_type="bearer")
