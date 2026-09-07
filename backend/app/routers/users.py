from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user, roles
from ..models import (
    User, ParentStudent, TeacherClass, ClassSchedule,
    NotificationSetting, Notification, Attendance, AttendanceEvent, RegistrationCode
)
from ..schemas import UserOut, UserUpdate
from ..security import hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "telegram_id": user.telegram_id,
        "telegram_username": user.telegram_username,
    }


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user: User = Depends(roles("ADMIN"))):
    return db.query(User).order_by(User.role, User.full_name).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(roles("ADMIN"))):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    return u


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), user: User = Depends(roles("ADMIN"))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")

    dump = data.model_dump(exclude_unset=True)

    if "email" in dump and dump["email"] and dump["email"] != target.email:
        conflict = db.query(User).filter(User.email == dump["email"], User.id != user_id).first()
        if conflict:
            raise HTTPException(409, f"Email '{dump['email']}' is already in use by another user")

    if "password" in dump and dump["password"]:
        target.password_hash = hash_password(dump.pop("password"))
    elif "password" in dump:
        dump.pop("password")

    for k, v in dump.items():
        setattr(target, k, v)

    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(roles("ADMIN"))):
    if user.id == user_id:
        raise HTTPException(400, "You cannot delete your own logged-in account")

    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")

    if target.role == "ADMIN":
        admin_count = db.query(User).filter(User.role == "ADMIN", User.status == "ACTIVE").count()
        if admin_count <= 1:
            raise HTTPException(400, "Cannot delete the only remaining active Administrator account")

    # Clean up dependent relations
    db.query(ParentStudent).filter(ParentStudent.parent_id == user_id).delete(synchronize_session=False)
    db.query(TeacherClass).filter(TeacherClass.teacher_id == user_id).delete(synchronize_session=False)
    db.query(NotificationSetting).filter(NotificationSetting.parent_id == user_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.parent_id == user_id).delete(synchronize_session=False)

    # Nullify references in schedules, attendance, codes
    schedules = db.query(ClassSchedule).filter(ClassSchedule.teacher_id == user_id).all()
    for s in schedules:
        s.teacher_id = None

    attendances = db.query(Attendance).filter(Attendance.recorded_by == user_id).all()
    for a in attendances:
        a.recorded_by = None

    events = db.query(AttendanceEvent).filter(AttendanceEvent.recorded_by == user_id).all()
    for e in events:
        e.recorded_by = None

    reg_codes = db.query(RegistrationCode).filter(RegistrationCode.created_by == user_id).all()
    for rc in reg_codes:
        rc.created_by = None

    name = target.full_name
    db.delete(target)
    db.commit()
    return {"message": f"User '{name}' deleted successfully", "id": user_id}
