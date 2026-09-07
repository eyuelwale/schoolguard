from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, UserOut, Token
from ..security import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/bootstrap-admin", response_model=UserOut)
def bootstrap_admin(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.role == "ADMIN").first():
        raise HTTPException(409, "An admin already exists")
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="ADMIN",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    if data.role.upper() not in {"PARENT", "TEACHER", "SECURITY"}:
        raise HTTPException(400, "Self-registration is only allowed for parent/teacher/security in this demo")
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role.upper(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_phone_variants(phone_str: str) -> list[str]:
    digits = "".join(c for c in phone_str if c.isdigit())
    if not digits:
        return [phone_str.strip()]
    variants = {phone_str.strip(), digits, "+" + digits}
    if digits.startswith("251") and len(digits) >= 11:
        local = "0" + digits[3:]
        variants.add(local)
        variants.add(digits[3:])
    elif digits.startswith("0") and len(digits) >= 9:
        raw = digits[1:]
        variants.add(raw)
        variants.add("251" + raw)
        variants.add("+251" + raw)
    elif len(digits) == 9:
        variants.add("0" + digits)
        variants.add("251" + digits)
        variants.add("+251" + digits)
    return list(variants)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    ident = data.email.strip()
    phone_variants = get_phone_variants(ident)

    # Match by email, normalized phone, or Telegram username
    user = db.query(User).filter(
        (User.email == ident) |
        (User.phone.in_(phone_variants)) |
        (User.telegram_username == ident.lstrip("@"))
    ).first()

    # If user typed 'admin', match active administrator
    if not user and ident.lower() == "admin":
        user = db.query(User).filter(User.role == "ADMIN", User.status == "ACTIVE").first()
        if not user:
            user = db.query(User).filter(User.role == "ADMIN").first()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return Token(access_token=create_token(user.id, user.role))
