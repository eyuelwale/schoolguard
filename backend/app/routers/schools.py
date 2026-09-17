from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles
from ..models import School, ClassRoom, Student, User
from ..schemas import SchoolCreate, SchoolUpdate, SchoolOut

router = APIRouter(prefix="/api/schools", tags=["Schools"])


@router.post("/", response_model=SchoolOut)
def create(data: SchoolCreate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    existing = db.query(School).filter(School.code == data.code).first()
    if existing:
        raise HTTPException(409, f"School code '{data.code}' is already registered")
    obj = School(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[SchoolOut])
def list_schools(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    return db.query(School).all()


@router.get("/{school_id}", response_model=SchoolOut)
def get_school(school_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    return school


@router.put("/{school_id}", response_model=SchoolOut)
def update_school(school_id: int, data: SchoolUpdate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")

    dump = data.model_dump(exclude_unset=True)
    if "code" in dump and dump["code"] != school.code:
        conflict = db.query(School).filter(School.code == dump["code"], School.id != school_id).first()
        if conflict:
            raise HTTPException(409, f"School code '{dump['code']}' is already in use by another school")

    for k, v in dump.items():
        setattr(school, k, v)

    db.commit()
    db.refresh(school)
    return school


@router.delete("/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")

    count_classes = db.query(ClassRoom).filter(ClassRoom.school_id == school_id).count()
    count_students = db.query(Student).filter(Student.school_id == school_id).count()
    count_users = db.query(User).filter(User.school_id == school_id).count()

    if count_classes > 0 or count_students > 0 or count_users > 0:
        details = []
        if count_classes: details.append(f"{count_classes} class(es)")
        if count_students: details.append(f"{count_students} student(s)")
        if count_users: details.append(f"{count_users} user(s)")
        raise HTTPException(
            400,
            f"Cannot delete school '{school.name}' because {', '.join(details)} are linked to it. Please reassign or remove them first."
        )

    db.delete(school)
    db.commit()
    return {"message": f"School '{school.name}' successfully deleted", "id": school_id}
