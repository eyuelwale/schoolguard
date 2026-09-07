import os
import time
from datetime import datetime, date
import logging
import httpx
from sqlalchemy.orm import Session
from .config import settings
from .models import Attendance, AttendanceEvent, NotificationSetting, Notification, ParentStudent, Student, User

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

logger = logging.getLogger(__name__)


def send_telegram_message(telegram_id: int, message: str, retries: int = 3, timeout: float = 30.0) -> tuple[bool, str | None]:
    """Sends a notification message to a parent's Telegram chat with automatic retries and extended timeout."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False, "TELEGRAM_BOT_TOKEN is not configured in .env"
    if not telegram_id:
        return False, "Parent does not have a linked telegram_id"

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
    }
    
    last_error = "Unknown error"
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return True, None
                elif resp.status_code == 429:
                    retry_after = 2
                    try:
                        retry_after = int(resp.json().get("parameters", {}).get("retry_after", 2))
                    except Exception:
                        pass
                    last_error = f"Telegram rate limit hit (429). Retrying in {retry_after}s..."
                    logger.warning(f"Telegram rate limited for chat {telegram_id}: {last_error}")
                    if attempt < retries:
                        time.sleep(retry_after)
                        continue
                else:
                    data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
                    err_desc = data.get("description", resp.text)
                    last_error = f"Telegram error: {err_desc}"
                    logger.warning(f"Telegram API error (attempt {attempt}/{retries}) for chat {telegram_id}: {err_desc}")
                    # Don't retry if chat doesn't exist or bot is blocked
                    if resp.status_code in {400, 403}:
                        return False, err_desc
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            last_error = f"Telegram connection timed out ({type(e).__name__}). Retrying ({attempt}/{retries})..."
            logger.warning(f"Attempt {attempt}/{retries} timed out for chat {telegram_id}: {e}")
        except httpx.ConnectError as e:
            last_error = "Could not connect to api.telegram.org. If Telegram is blocked by network firewall, check connectivity or proxy."
            logger.warning(f"Attempt {attempt}/{retries} connect error for chat {telegram_id}: {e}")
        except Exception as e:
            last_error = f"Failed to send Telegram message: {str(e)}"
            logger.warning(f"Attempt {attempt}/{retries} error for chat {telegram_id}: {e}")

        if attempt < retries:
            time.sleep(1.5 * attempt)

    return False, last_error


from concurrent.futures import ThreadPoolExecutor

# Background thread pool to send notifications asynchronously without blocking web requests
_notification_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="notif-worker")


def _send_telegram_worker(notif_id: int, telegram_id: int, message: str):
    """Background worker task that sends Telegram message and updates Notification status."""
    from .database import SessionLocal
    from .models import Notification
    try:
        success, err = send_telegram_message(telegram_id, message)
        db = SessionLocal()
        try:
            notif = db.get(Notification, notif_id)
            if notif:
                if success:
                    notif.status = "SENT"
                    notif.sent_at = datetime.utcnow()
                    notif.error_message = None
                else:
                    notif.status = "FAILED"
                    notif.error_message = err
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Background worker failed for notification {notif_id}: {e}")


def dispatch_notification_async(notif_id: int, telegram_id: int, message: str):
    """Submits a notification to the background pool for immediate non-blocking delivery."""
    _notification_pool.submit(_send_telegram_worker, notif_id, telegram_id, message)


def resend_notification_record(db: Session, notif: Notification, async_dispatch: bool = False) -> tuple[bool, str | None]:
    """Resends an existing notification record to the parent's Telegram account and updates its delivery status."""
    parent = None
    if notif.parent_id:
        parent = db.get(User, notif.parent_id)
    if not parent and notif.student_id:
        parent_ids = parent_ids_for_student(db, notif.student_id)
        if parent_ids:
            parent = db.get(User, parent_ids[0])
            if parent:
                notif.parent_id = parent.id

    if not parent:
        notif.status = "FAILED"
        notif.error_message = "No parent associated with this notification"
        db.commit()
        return False, notif.error_message

    if not parent.telegram_id:
        notif.status = "FAILED"
        notif.error_message = f"Parent {parent.full_name} does not have a linked Telegram account"
        db.commit()
        return False, notif.error_message

    # Format message
    msg_text = notif.message
    if not msg_text.startswith("🔔"):
        msg_text = f"🔔 <b>SchoolGuard Alert (Resent)</b>\n\n{msg_text}"

    if async_dispatch:
        notif.status = "PENDING"
        notif.error_message = None
        db.commit()
        dispatch_notification_async(notif.id, parent.telegram_id, msg_text)
        return True, None

    success, err = send_telegram_message(parent.telegram_id, msg_text)
    if success:
        notif.status = "SENT"
        notif.sent_at = datetime.utcnow()
        notif.error_message = None
    else:
        notif.status = "FAILED"
        notif.error_message = err

    db.commit()
    db.refresh(notif)
    return success, err


def attendance_for_day(db, student_id, day):
    obj = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.attendance_date == day,
    ).first()
    if not obj:
        obj = Attendance(student_id=student_id, attendance_date=day)
        db.add(obj)
        db.flush()
    return obj


def parent_ids_for_student(db: Session, student_id: int):
    return [
        row.parent_id
        for row in db.query(ParentStudent).filter(
            ParentStudent.student_id == student_id
        ).all()
    ]


def enqueue_notifications(db: Session, student: Student, kind: str, message: str):
    flag = {
        "ARRIVAL": "arrival_enabled",
        "DEPARTURE": "departure_enabled",
        "LATE": "late_enabled",
        "ABSENCE": "absence_enabled",
        "CLASS_END": "class_end_enabled",
    }.get(kind)

    for parent_id in parent_ids_for_student(db, student.id):
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.parent_id == parent_id,
            NotificationSetting.student_id == student.id,
        ).first()

        enabled = True if not setting or not flag else getattr(setting, flag)
        if enabled:
            parent = db.get(User, parent_id)
            notif = Notification(
                parent_id=parent_id,
                student_id=student.id,
                type=kind,
                title=f"SchoolGuard: {kind.title()}",
                message=message,
                status="PENDING",
            )
            db.add(notif)
            db.flush()

            if parent and parent.telegram_id:
                formatted_msg = f"🔔 <b>SchoolGuard Alert</b>\n\n{message}"
                # Immediately hand off to background pool - zero HTTP latency!
                dispatch_notification_async(notif.id, parent.telegram_id, formatted_msg)


def mark_arrival(db: Session, student_id: int, actor_id: int, method: str, when: datetime):
    student = db.get(Student, student_id)
    if not student:
        raise ValueError("Student not found")

    a = attendance_for_day(db, student_id, when.date())
    is_update = a.arrival_time is not None

    a.arrival_time = when
    a.arrival_method = method
    a.recorded_by = actor_id
    a.status = "PRESENT"
    # If student is checking in again after previously departing, reset departure
    if a.departure_time and a.departure_time <= when:
        a.departure_time = None

    db.add(AttendanceEvent(
        student_id=student_id,
        event_type="ARRIVAL",
        event_time=when,
        method=method,
        recorded_by=actor_id,
    ))

    arrival_label = "Arrival Updated / Re-entry" if is_update else "Arrival Recorded"
    enqueue_notifications(
        db,
        student,
        "ARRIVAL",
        f"✅ <b>{arrival_label}</b>\n"
        f"Student: <b>{student.notification_name}</b> (Code: {student.student_code})\n"
        f"📅 Date: {when.strftime('%Y-%m-%d')}\n"
        f"⏰ <b>Arrival Time:</b> {when.strftime('%I:%M:%S %p')}\n"
        f"📋 Method: {method or 'Gate Check'}"
    )

    db.commit()
    db.refresh(a)
    return a


def mark_departure(db: Session, student_id: int, actor_id: int, method: str, when: datetime):
    student = db.get(Student, student_id)
    if not student:
        raise ValueError("Student not found")

    a = attendance_for_day(db, student_id, when.date())
    if not a.arrival_time:
        # If departure is marked before arrival, set arrival to current time
        a.arrival_time = when

    is_update = a.departure_time is not None
    a.departure_time = when
    a.departure_method = method
    a.recorded_by = actor_id

    db.add(AttendanceEvent(
        student_id=student_id,
        event_type="DEPARTURE",
        event_time=when,
        method=method,
        recorded_by=actor_id,
    ))

    arrival_str = a.arrival_time.strftime('%I:%M:%S %p') if a.arrival_time else "N/A"
    departure_str = when.strftime('%I:%M:%S %p')
    departure_label = "Departure Updated" if is_update else "Departure Recorded"

    enqueue_notifications(
        db,
        student,
        "DEPARTURE",
        f"✅ <b>{departure_label}</b>\n"
        f"Student: <b>{student.notification_name}</b> (Code: {student.student_code})\n"
        f"📅 Date: {when.strftime('%Y-%m-%d')}\n"
        f"⏰ <b>Arrival Time:</b> {arrival_str}\n"
        f"⏰ <b>Departure Time:</b> {departure_str}\n"
        f"📋 Method: {method or 'Gate Check'}"
    )

    db.commit()
    db.refresh(a)
    return a
