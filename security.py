from datetime import datetime, timedelta, timezone
from typing import Optional

import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Member

# Load .env locally; in App Runner you'll set env vars directly
load_dotenv()

# --- JWT settings ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set in environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Used by Swagger / dependencies to read Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Optional token reader that NEVER throws 401
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_member(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Member:
    """
    Dependency to get the currently authenticated member from the JWT.
    Use this in any protected endpoint.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Member).filter(Member.email == email).first()
    if user is None:
        raise credentials_exception

    return user

def get_current_member_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional),
):
    """
    Optional authentication.
    Returns Member if token is valid.
    Returns None if no token or invalid token.
    Never raises 401.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user = db.query(Member).filter(Member.email == email).first()
    return user
