from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import roles, current_user
from ..models import NotificationSetting, ParentStudent, Notification, User
from ..schemas import NotificationSettingsIn, BulkDeleteIn
from ..services import send_telegram_message, resend_notification_record

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/settings")
def settings(data: NotificationSettingsIn, db: Session = Depends(get_db), user=Depends(roles("PARENT"))):
    linked = db.query(ParentStudent).filter(
        ParentStudent.parent_id == user.id,
        ParentStudent.student_id == data.student_id
    ).first()
    if not linked:
        raise HTTPException(403, "Student is not linked to your account")
    obj = db.query(NotificationSetting).filter(
        NotificationSetting.parent_id == user.id,
        NotificationSetting.student_id == data.student_id
    ).first()
    if not obj:
        obj = NotificationSetting(parent_id=user.id, **data.model_dump())
        db.add(obj)
    else:
        for k, v in data.model_dump().items():
            setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.get("/logs")
def notification_logs(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Retrieve recent notification history."""
    return db.query(Notification).order_by(Notification.created_at.desc()).limit(100).all()


@router.post("/test/{parent_id}")
def send_test_notification(parent_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Dispatches an immediate test push notification to a parent's Telegram account."""
    parent = db.get(User, parent_id)
    if not parent:
        raise HTTPException(404, "Parent not found")
    if not parent.telegram_id:
        raise HTTPException(400, "Parent does not have a linked Telegram ID yet")

    lang = (getattr(parent, "language", None) or "en").lower()
    if lang == "am":
        msg = f"🔔 <b>የስኩልጋርድ የሙከራ ማሳወቂያ</b>\n\nሰላም {parent.full_name}፣ ይህ ከ SchoolGuard ሥርዓት የተላከ የሙከራ ማሳወቂያ ነው።"
        title = "ስኩልጋርድ: የሙከራ ማሳወቂያ"
    else:
        msg = f"🔔 <b>SchoolGuard Test Alert</b>\n\nHello {parent.full_name}, this is a test notification from the SchoolGuard system."
        title = "SchoolGuard: Test Alert"

    success, err = send_telegram_message(parent.telegram_id, msg)

    notif = Notification(
        parent_id=parent.id,
        student_id=None,
        type="TEST",
        title=title,
        message=msg,
        status="SENT" if success else "FAILED",
        sent_at=datetime.utcnow() if success else None,
        error_message=err,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    if not success:
        raise HTTPException(502, f"Failed to send to Telegram: {err}")

    return {"message": "Test notification sent successfully to Telegram!", "notification_id": notif.id}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Delete an individual notification log."""
    notif = db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(404, "Notification log record not found")
    db.delete(notif)
    db.commit()
    return {"message": "Notification log deleted successfully", "id": notification_id}


@router.post("/bulk-delete")
@router.delete("/bulk-delete")
def bulk_delete_notifications(data: BulkDeleteIn, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Delete multiple notification logs in bulk."""
    if not data.ids:
        raise HTTPException(400, "No notification IDs provided for deletion")
    count = db.query(Notification).filter(Notification.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Successfully deleted {count} notification record(s)", "deleted_count": count}


@router.post("/resend/{notification_id}")
def resend_notification(notification_id: int, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Resend a specific notification log to the parent's Telegram account."""
    notif = db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(404, "Notification log record not found")

    success, err = resend_notification_record(db, notif)
    if not success:
        raise HTTPException(502, f"Failed to deliver notification to parent: {err}")

    return {
        "message": f"Notification #{notif.id} successfully redelivered to parent!",
        "notification_id": notif.id,
        "status": notif.status
    }


@router.post("/bulk-resend")
def bulk_resend_notifications(data: BulkDeleteIn, db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Resend multiple notification logs in bulk."""
    if not data.ids:
        raise HTTPException(400, "No notification IDs provided for resending")

    notifs = db.query(Notification).filter(Notification.id.in_(data.ids)).all()
    success_count = 0
    fail_count = 0
    errors = []

    for notif in notifs:
        s, err = resend_notification_record(db, notif, async_dispatch=True)
        if s:
            success_count += 1
        else:
            fail_count += 1
            if err and err not in errors:
                errors.append(err)

    msg = f"Dispatched redelivery for {success_count} notification(s) in the background"
    if fail_count > 0:
        err_hint = f" ({'; '.join(errors[:2])})" if errors else ""
        msg += f", {fail_count} could not be dispatched{err_hint}"

    return {
        "message": msg,
        "success_count": success_count,
        "fail_count": fail_count
    }


@router.post("/retry-all-failed")
def retry_all_failed_notifications(db: Session = Depends(get_db), user=Depends(roles("ADMIN"))):
    """Automatically find all failed or pending notifications and re-attempt delivery in the background."""
    failed_notifs = db.query(Notification).filter(
        Notification.status.in_(["FAILED", "PENDING"])
    ).order_by(Notification.created_at.desc()).limit(50).all()

    if not failed_notifs:
        return {"message": "No failed or pending notifications to retry.", "success_count": 0, "fail_count": 0}

    success_count = 0
    fail_count = 0
    errors = []

    for notif in failed_notifs:
        s, err = resend_notification_record(db, notif, async_dispatch=True)
        if s:
            success_count += 1
        else:
            fail_count += 1
            if err and err not in errors:
                errors.append(err)

    msg = f"Dispatched background redelivery for {success_count} notification(s)"
    if fail_count > 0:
        err_hint = f" ({'; '.join(errors[:2])})" if errors else ""
        msg += f", {fail_count} could not be dispatched{err_hint}"

    return {
        "message": msg,
        "success_count": success_count,
        "fail_count": fail_count
    }



