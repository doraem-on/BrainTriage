from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import verify_credentials, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": create_access_token(payload.username), "token_type": "bearer"}


@router.get("/me")
def me(username: str = Depends(get_current_user)):
    return {"username": username}
