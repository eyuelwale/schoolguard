from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles, current_user
from ..models import ParentStudent, Student, User, NotificationSetting
from ..schemas import LinkStudent, ParentLinkOut, ParentLinkUpdate

router = APIRouter(prefix="/api/parents", tags=["Parents"])


@router.post("/link-student")
def link(data: LinkStudent, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    if not db.get(Student, data.student_id):
        raise HTTPException(404, "Student not found")
    if not db.get(User, data.parent_id):
        raise HTTPException(404, "Parent not found")
    obj = ParentStudent(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Parent is already linked to this student")
    return {"message": "Parent linked to student"}


@router.get("/links", response_model=list[ParentLinkOut])
def list_links(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    rows = db.query(ParentStudent).all()
    results = []
    for r in rows:
        p = db.get(User, r.parent_id)
        s = db.get(Student, r.student_id)
        if p and s:
            results.append(ParentLinkOut(
                id=r.id,
                parent_id=r.parent_id,
                student_id=r.student_id,
                parent_name=p.full_name,
                parent_email=p.email,
                parent_phone=p.phone,
                student_name=s.notification_name,
                student_code=s.student_code,
                relationship_type=r.relationship_type,
                is_primary=r.is_primary,
            ))
    return results


@router.put("/links/{link_id}")
def update_link(link_id: int, data: ParentLinkUpdate, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    link_obj = db.get(ParentStudent, link_id)
    if not link_obj:
        raise HTTPException(404, "Parent-student link not found")
    dump = data.model_dump(exclude_unset=True)
    for k, v in dump.items():
        setattr(link_obj, k, v)
    db.commit()
    return {"message": "Parent-student link updated", "id": link_id}


@router.delete("/links/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    link_obj = db.get(ParentStudent, link_id)
    if not link_obj:
        raise HTTPException(404, "Parent-student link not found")
    db.delete(link_obj)
    db.commit()
    return {"message": "Student unlinked from parent", "id": link_id}


@router.get("/my-children")
def my_children(db: Session = Depends(get_db), user=Depends(roles("PARENT"))):
    rows = db.query(ParentStudent).filter(ParentStudent.parent_id == user.id).all()
    return [
        {
            "id": r.student.id,
            "student_code": r.student.student_code,
            "name": f"{r.student.first_name} {r.student.middle_name or ''} {r.student.last_name or ''}".strip(),
            "class_id": r.student.class_id,
        }
        for r in rows if r.student
    ]
