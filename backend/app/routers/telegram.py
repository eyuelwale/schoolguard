from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles, current_user
from ..models import User
from ..schemas import TelegramLinkIn

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])


@router.post("/link-self")
def link_self(data: TelegramLinkIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Any authenticated user can link their own Telegram account."""
    # Check if telegram_id is already taken by another user
    existing = db.query(User).filter(User.telegram_id == data.telegram_id, User.id != user.id).first()
    if existing:
        raise HTTPException(409, "This Telegram account is already linked to another user")
    target = db.get(User, user.id)
    target.telegram_id = data.telegram_id
    target.telegram_username = data.telegram_username
    if data.language:
        target.language = data.language
    db.commit()
    return {"message": "Telegram account linked successfully"}


@router.post("/set-language")
def set_language(data: TelegramLinkIn, db: Session = Depends(get_db)):
    """Set language preference for a telegram user."""
    user = db.query(User).filter(User.telegram_id == data.telegram_id).first()
    if not user:
        raise HTTPException(404, "Telegram account not linked to any user")
    if data.language:
        user.language = data.language
        db.commit()
    return {"message": "Language updated successfully", "language": user.language}


@router.post("/link")
def link_telegram(data: TelegramLinkIn, parent_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Admin links a specific parent's Telegram account by parent_id."""
    target = db.get(User, parent_id)
    if not target:
        raise HTTPException(404, "User not found")
    target.telegram_id = data.telegram_id
    target.telegram_username = data.telegram_username
    if data.language:
        target.language = data.language
    db.commit()
    return {"message": f"Telegram linked to {target.full_name}"}
