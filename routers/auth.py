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
# Validate Google ID Token (DEBUG ADDED)
# ---------------------------------------------------------
def verify_google_id_token(id_token: str):
    try:
        print("\nDEBUG: Verifying Google token...")
        resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
        print("DEBUG: Google raw response:", resp.text)

        if resp.status_code != 200:
            print("DEBUG: Google returned non-200")
            return None

        data = resp.json()

        if "email" not in data:
            print("DEBUG: Google token missing email field")
            return None

        # Ensure correct audience
        print(" DEBUG: Expected AUD:", GOOGLE_WEB_CLIENT_ID)
        print(" DEBUG: Actual AUD:", data.get("aud"))

        if GOOGLE_WEB_CLIENT_ID and data.get("aud") != GOOGLE_WEB_CLIENT_ID:
            print(" DEBUG: AUD mismatch")
            return None

        print(" DEBUG: Google token validated OK")
        return data

    except Exception as e:
        print(" ERROR verify_google_id_token:", e)
        return None



# ---------------------------------------------------------
# POST /auth/google (DEBUG ADDED)
# ---------------------------------------------------------
@router.post("/google", response_model=AuthResponse)
def login_with_google(
    payload: SocialLoginRequest,
    db: Session = Depends(get_db)
):

    print("\n\n==============================")
    print(" DEBUG: /auth/google called")
    print("==============================")
    print("Payload:", payload)

    # Verify ID token
    data = verify_google_id_token(payload.id_token)
    if not data:
        print("DEBUG: Token verification failed")
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = data["email"].lower()
    name = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()

    print(" DEBUG: Google email =", email)
    print(" DEBUG: Google name =", name)

    # Find existing member
    member = db.query(Member).filter(Member.email == email).first()

    if not member:
        print(" DEBUG: Creating NEW member")
        member = Member(
            email=email,
            name=name,
            platform="google",
            status="new_user",
        )
        db.add(member)
        db.commit()
        db.refresh(member)
    else:
        print(" DEBUG: Existing member found → ID:", member.members_id)
        print(" DEBUG: Existing status:", member.status)

    # Handle status
    print(" DEBUG: RETURNING STATUS:", member.status)

    # Return response
    response = {
        "status": member.status,
        "access_token": None,
        "token_type": None,
        "member": MemberOut.model_validate(member)
    }

    if member.status in ["new_user", "verified"]:
        token = create_access_token({"sub": member.email})
        response["access_token"] = token
        response["token_type"] = "bearer"

    print(" DEBUG: Final Response Body:", response)
    print("====================================\n")

    return response
