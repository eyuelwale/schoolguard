from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or user.status != "ACTIVE":
        raise HTTPException(401, "User not found or inactive")
    return user


def roles(*allowed):
    def checker(user: User = Depends(current_user)):
        if user.role not in allowed:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker
