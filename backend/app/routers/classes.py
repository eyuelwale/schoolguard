from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles
from ..models import ClassRoom, TeacherClass, ClassSchedule, Student, User
from ..schemas import ClassCreate, ClassUpdate, ClassOut, AssignTeacher

router = APIRouter(prefix="/api/classes", tags=["Classes"])


@router.post("/", response_model=ClassOut)
def create(data: ClassCreate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    existing = db.query(ClassRoom).filter(
        ClassRoom.school_id == data.school_id,
        ClassRoom.class_code == data.class_code
    ).first()
    if existing:
        raise HTTPException(409, f"Class code '{data.class_code}' is already registered in this school")
    obj = ClassRoom(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ClassOut])
def list_classes(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    return db.query(ClassRoom).all()


@router.post("/assign-teacher")
def assign_teacher(data: AssignTeacher, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    teacher = db.get(User, data.teacher_id)
    classroom = db.get(ClassRoom, data.class_id)
    if not teacher or teacher.role != "TEACHER":
        raise HTTPException(404, "Teacher not found")
    if not classroom:
        raise HTTPException(404, "Class not found")
    obj = TeacherClass(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Teacher is already assigned to this class")
    return {"message": "Teacher assigned"}


@router.get("/teacher-assignments")
def list_teacher_assignments(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    assignments = db.query(TeacherClass).all()
    results = []
    for a in assignments:
        t = db.get(User, a.teacher_id)
        c = db.get(ClassRoom, a.class_id)
        if t and c:
            results.append({
                "id": a.id,
                "teacher_id": a.teacher_id,
                "teacher_name": t.full_name,
                "teacher_email": t.email,
                "class_id": a.class_id,
                "class_name": c.class_name,
                "class_code": c.class_code,
                "academic_year": a.academic_year,
            })
    return results


@router.delete("/teacher-assignments/{assignment_id}")
def delete_teacher_assignment(assignment_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    assignment = db.get(TeacherClass, assignment_id)
    if not assignment:
        raise HTTPException(404, "Teacher assignment not found")
    db.delete(assignment)
    db.commit()
    return {"message": "Teacher unassigned from class", "id": assignment_id}


@router.get("/{class_id}", response_model=ClassOut)
def get_class(class_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    classroom = db.get(ClassRoom, class_id)
    if not classroom:
        raise HTTPException(404, "Class not found")
    return classroom


@router.put("/{class_id}", response_model=ClassOut)
def update_class(class_id: int, data: ClassUpdate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    classroom = db.get(ClassRoom, class_id)
    if not classroom:
        raise HTTPException(404, "Class not found")

    dump = data.model_dump(exclude_unset=True)
    if "class_code" in dump and dump["class_code"] != classroom.class_code:
        target_school = dump.get("school_id", classroom.school_id)
        conflict = db.query(ClassRoom).filter(
            ClassRoom.school_id == target_school,
            ClassRoom.class_code == dump["class_code"],
            ClassRoom.id != class_id
        ).first()
        if conflict:
            raise HTTPException(409, f"Class code '{dump['class_code']}' is already in use in this school")

    for k, v in dump.items():
        setattr(classroom, k, v)

    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    classroom = db.get(ClassRoom, class_id)
    if not classroom:
        raise HTTPException(404, "Class not found")

    # Clean up dependent assignments & schedules
    db.query(TeacherClass).filter(TeacherClass.class_id == class_id).delete(synchronize_session=False)
    db.query(ClassSchedule).filter(ClassSchedule.class_id == class_id).delete(synchronize_session=False)

    # Detach students from this class instead of deleting them
    students = db.query(Student).filter(Student.class_id == class_id).all()
    for s in students:
        s.class_id = None

    name = classroom.class_name
    db.delete(classroom)
    db.commit()
    return {"message": f"Class '{name}' deleted successfully", "id": class_id}
