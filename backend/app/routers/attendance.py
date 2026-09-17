from datetime import datetime, date as date_type
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles
from ..models import Attendance, Student
from ..schemas import (
    AttendanceArrival, AttendanceDeparture, AttendanceStatus, AttendanceOut,
    BulkAttendanceIn, AttendanceUpdate
)
from ..services import (
    mark_arrival, mark_departure, enqueue_notifications, attendance_for_day,
    build_arrival_message, build_departure_message, build_status_message
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

@router.post("/arrival", response_model=AttendanceOut)
def arrival(data: AttendanceArrival, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    try:
        return mark_arrival(db, data.student_id, user.id, data.method, data.arrival_time or datetime.now())
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/departure", response_model=AttendanceOut)
def departure(data: AttendanceDeparture, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    try:
        return mark_departure(db, data.student_id, user.id, data.method, data.departure_time or datetime.now())
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.put("/status", response_model=AttendanceOut)
def status(data: AttendanceStatus, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    allowed = {"PRESENT","ABSENT","LATE","EXCUSED"}
    value = data.status.upper()
    if value not in allowed:
        raise HTTPException(400, "Invalid status")
    a = db.query(Attendance).filter(
        Attendance.student_id == data.student_id,
        Attendance.attendance_date == date_type.today()
    ).first()
    if not a:
        a = Attendance(student_id=data.student_id, attendance_date=date_type.today())
        db.add(a)
    a.status = value
    a.recorded_by = user.id

    student = db.get(Student, data.student_id)
    if student:
        kind = "LATE" if value == "LATE" else "ABSENCE" if value == "ABSENT" else "ARRIVAL"
        msg_dict = build_status_message(
            student=student,
            status_val=value,
            date_val=date_type.today(),
            arrival_time=a.arrival_time,
            departure_time=a.departure_time,
            recorder_name=user.full_name,
        )
        enqueue_notifications(
            db,
            student,
            kind,
            msg_dict,
        )

    db.commit(); db.refresh(a)
    return a


@router.post("/bulk", response_model=list[AttendanceOut])
def bulk_attendance(data: BulkAttendanceIn, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Bulk arrival, departure, or roll-call status for multiple students on a given date."""
    event = data.event_type.upper()
    if event not in {"ARRIVAL", "DEPARTURE", "STATUS"}:
        raise HTTPException(400, "event_type must be ARRIVAL, DEPARTURE, or STATUS")
    if event == "STATUS":
        allowed_statuses = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
        val = (data.status or "").upper()
        if val not in allowed_statuses:
            raise HTTPException(400, f"status must be one of {allowed_statuses}")


    when = data.event_time or datetime.now()

    results = []
    for student_id in data.student_ids:
        student = db.get(Student, student_id)
        if not student:
            continue

        a = attendance_for_day(db, student_id, data.attendance_date)
        a.recorded_by = user.id

        if event == "ARRIVAL":
            a.arrival_time = when
            a.arrival_method = data.method
            a.status = "PRESENT"
            # If student is checking in again after previously departing, reset departure
            if a.departure_time and a.departure_time <= when:
                a.departure_time = None

            msg_dict = build_arrival_message(student, when, is_update=False, recorder_name=user.full_name)
            enqueue_notifications(db, student, "ARRIVAL", msg_dict)

        elif event == "DEPARTURE":
            if not a.arrival_time:
                # If student was marked present/late via roll call without gate check-in, set arrival time
                if a.status in {"PRESENT", "LATE"}:
                    a.arrival_time = when
                else:
                    # Guard: can't depart if absent or never attended
                    continue
            a.departure_time = when
            a.departure_method = data.method

            msg_dict = build_departure_message(student, when, arrival_time=a.arrival_time, is_update=False, recorder_name=user.full_name)
            enqueue_notifications(db, student, "DEPARTURE", msg_dict)

        else:  # STATUS  roll-call: set status directly
            val = data.status.upper()
            a.status = val

            kind = "LATE" if val == "LATE" else "ABSENCE" if val == "ABSENT" else "ARRIVAL"
            msg_dict = build_status_message(
                student=student,
                status_val=val,
                date_val=data.attendance_date,
                arrival_time=a.arrival_time,
                departure_time=a.departure_time,
                recorder_name=user.full_name,
            )
            enqueue_notifications(db, student, kind, msg_dict)

        results.append(a)


    db.commit()
    for a in results:
        db.refresh(a)
    return results




@router.get("/today", response_model=list[AttendanceOut])
def today(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    return db.query(Attendance).filter(Attendance.attendance_date == date_type.today()).all()

@router.get("/date/{target_date}", response_model=list[AttendanceOut])
def by_date(target_date: date_type, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    return db.query(Attendance).filter(Attendance.attendance_date == target_date).all()

@router.get("/student/{student_id}", response_model=list[AttendanceOut])
def history(student_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    return db.query(Attendance).filter(Attendance.student_id == student_id).order_by(Attendance.attendance_date.desc()).limit(100).all()


@router.put("/{attendance_id}", response_model=AttendanceOut)
def update_attendance(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    rec = db.get(Attendance, attendance_id)
    if not rec:
        raise HTTPException(404, "Attendance record not found")

    dump = data.model_dump(exclude_unset=True)
    for k, v in dump.items():
        setattr(rec, k, v)
    rec.recorded_by = user.id

    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    rec = db.get(Attendance, attendance_id)
    if not rec:
        raise HTTPException(404, "Attendance record not found")
    db.delete(rec)
    db.commit()
    return {"message": "Attendance record deleted", "id": attendance_id}


