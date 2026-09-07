import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles
from ..models import (
    Student, ParentStudent, NotificationSetting,
    Attendance, AttendanceEvent, Notification, RegistrationCode
)
from ..schemas import StudentCreate, StudentUpdate, StudentOut

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.post("/", response_model=StudentOut)
def create(data: StudentCreate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    existing = db.query(Student).filter(
        Student.school_id == data.school_id,
        Student.student_code == data.student_code
    ).first()
    if existing:
        raise HTTPException(409, f"Student code '{data.student_code}' is already registered in this school")
    obj = Student(**data.model_dump(), qr_token=secrets.token_urlsafe(32))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db), user=Depends(roles("ADMIN", "TEACHER"))):
    return db.query(Student).all()


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN", "TEACHER", "PARENT"))):
    obj = db.get(Student, student_id)
    if not obj:
        raise HTTPException(404, "Student not found")
    return obj


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    dump = data.model_dump(exclude_unset=True)
    if "student_code" in dump and dump["student_code"] != student.student_code:
        conflict = db.query(Student).filter(
            Student.student_code == dump["student_code"],
            Student.id != student_id
        ).first()
        if conflict:
            raise HTTPException(409, f"Student code '{dump['student_code']}' is already in use by another student")

    for k, v in dump.items():
        setattr(student, k, v)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    # Clean up dependent records
    db.query(ParentStudent).filter(ParentStudent.student_id == student_id).delete(synchronize_session=False)
    db.query(NotificationSetting).filter(NotificationSetting.student_id == student_id).delete(synchronize_session=False)
    db.query(AttendanceEvent).filter(AttendanceEvent.student_id == student_id).delete(synchronize_session=False)
    db.query(Attendance).filter(Attendance.student_id == student_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.student_id == student_id).delete(synchronize_session=False)
    db.query(RegistrationCode).filter(RegistrationCode.student_id == student_id).delete(synchronize_session=False)

    name = f"{student.first_name} {student.last_name or ''}".strip()
    db.delete(student)
    db.commit()
    return {"message": f"Student '{name}' deleted successfully", "id": student_id}
