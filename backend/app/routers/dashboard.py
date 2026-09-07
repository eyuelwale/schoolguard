from datetime import date
from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles
from ..models import Attendance, Student, ClassRoom

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/")
def dashboard(db: Session = Depends(get_db), user=Depends(roles("ADMIN","TEACHER"))):
    day = date.today()
    total = db.query(func.count(Student.id)).filter(Student.status=="ACTIVE").scalar() or 0
    present = db.query(func.count(Attendance.id)).filter(Attendance.attendance_date==day, Attendance.status=="PRESENT").scalar() or 0
    late = db.query(func.count(Attendance.id)).filter(Attendance.attendance_date==day, Attendance.status=="LATE").scalar() or 0
    absent = db.query(func.count(Attendance.id)).filter(Attendance.attendance_date==day, Attendance.status=="ABSENT").scalar() or 0
    classes = db.query(func.count(ClassRoom.id)).filter(ClassRoom.status=="ACTIVE").scalar() or 0
    return {"date": str(day), "total_students": total, "present": present, "late": late, "absent": absent, "classes": classes}
