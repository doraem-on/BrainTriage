"""Single-admin authentication, gating the whole clinical app behind a login.

This is a hackathon-appropriate auth model — one shared admin credential, not
a multi-user system — since the point is "keep patient data behind a login
screen for the demo," not role-based access control. Credentials and the
JWT signing secret come from backend/.env (see .env.example); the defaults
below exist so the app runs out of the box, but MUST be changed before any
real deployment.
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "braintriage2026")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-change-in-.env")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 12


def verify_credentials(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session")
    return payload["sub"]
