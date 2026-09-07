import os, sys
sys.path.insert(0, os.path.abspath("backend"))
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
try:
    if db.query(User).filter(User.role == "ADMIN").first():
        print("Admin already exists")
    else:
        email = input("Admin email: ").strip()
        password = input("Admin password: ").strip()
        name = input("Admin name: ").strip() or "School Administrator"
        db.add(User(full_name=name, email=email, password_hash=hash_password(password), role="ADMIN"))
        db.commit()
        print("Admin created.")
finally:
    db.close()
