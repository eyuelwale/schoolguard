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
    lang = (getattr(parent, "language", None) or "en").lower() if parent else "en"
    if not msg_text.startswith("🔔"):
        header = "🔔 <b>የስኩልጋርድ ማሳወቂያ (እንደገና የተላከ)</b>" if lang == "am" else "🔔 <b>SchoolGuard Alert (Resent)</b>"
        msg_text = f"{header}\n\n{msg_text}"

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


def translate_method(method: str | None) -> str:
    if not method:
        return "በር ላይ ፍተሻ"
    m = method.strip()
    m_lower = m.lower()
    if "qr" in m_lower:
        return "በ QR ኮድ"
    if "gate" in m_lower:
        return "በር ላይ ፍተሻ"
    if "manual" in m_lower:
        return "በእጅ ምዝገባ"
    if "roll" in m_lower:
        return "የክፍል ውስጥ ምዝገባ"
    if "bulk" in m_lower:
        return "በጅምላ"
    if "teacher" in m_lower:
        return "በአስተማሪ"
    if "security" in m_lower:
        return "በጥበቃ ሰራተኛ"
    if "admin" in m_lower:
        return "በአስተዳዳሪ"
    return m


def build_arrival_message(student: Student, when: datetime, method: str | None, is_update: bool = False) -> dict[str, str]:
    date_str = when.strftime('%Y-%m-%d')
    time_str = when.strftime('%I:%M %p')
    method_val = method or "Gate Check"
    method_am = translate_method(method_val)

    en_label = "Arrival Updated / Re-entry" if is_update else "Arrival Recorded"
    am_label = "የመግቢያ ሰዓት ተዘምኗል" if is_update else "ተማሪ ትምህርት ቤት ደርሷል / ገብቷል"

    en = (
        f"✅ <b>{en_label}</b>\n"
        f"Student: <b>{student.notification_name}</b> (Code: {student.student_code})\n"
        f"📅 Date: {date_str}\n"
        f"⏰ <b>Arrival Time:</b> {time_str}\n"
        f"📋 Method: {method_val}"
    )
    am = (
        f"✅ <b>{am_label}</b>\n"
        f"ተማሪ: <b>{student.notification_name}</b> (መለያ: {student.student_code})\n"
        f"📅 ቀን: {date_str}\n"
        f"⏰ <b>የመግቢያ ሰዓት:</b> {time_str}\n"
        f"📋 ዘዴ: {method_am}"
    )
    return {"en": en, "am": am}


def build_departure_message(student: Student, when: datetime, method: str | None, arrival_time: datetime | None, is_update: bool = False) -> dict[str, str]:
    date_str = when.strftime('%Y-%m-%d')
    dep_str = when.strftime('%I:%M %p')
    arr_str_en = arrival_time.strftime('%I:%M %p') if arrival_time else "Not recorded"
    arr_str_am = arrival_time.strftime('%I:%M %p') if arrival_time else "አልተመዘገበም"
    method_val = method or "Gate Check"
    method_am = translate_method(method_val)

    en_label = "Departure Updated" if is_update else "Departure Recorded"
    am_label = "የመውጫ ሰዓት ተዘምኗል" if is_update else "ተማሪ ከትምህርት ቤት ወጥቷል"

    en = (
        f"✅ <b>{en_label}</b>\n"
        f"Student: <b>{student.notification_name}</b> (Code: {student.student_code})\n"
        f"📅 Date: {date_str}\n"
        f"⏰ <b>Arrival Time:</b> {arr_str_en}\n"
        f"⏰ <b>Departure Time:</b> {dep_str}\n"
        f"📋 Method: {method_val}"
    )
    am = (
        f"✅ <b>{am_label}</b>\n"
        f"ተማሪ: <b>{student.notification_name}</b> (መለያ: {student.student_code})\n"
        f"📅 ቀን: {date_str}\n"
        f"⏰ <b>የመግቢያ ሰዓት:</b> {arr_str_am}\n"
        f"⏰ <b>የመውጫ ሰዓት:</b> {dep_str}\n"
        f"📋 ዘዴ: {method_am}"
    )
    return {"en": en, "am": am}


def build_status_message(student: Student, status_val: str, date_val: date, arrival_time: datetime | None, departure_time: datetime | None, method: str | None = None) -> dict[str, str]:
    status_val = status_val.upper()
    status_map_am = {
        "PRESENT": "ተገኝቷል",
        "LATE": "አርፍዷል",
        "ABSENT": "አልተገኘም",
        "EXCUSED": "ፈቃድ የተሰጠው",
    }
    status_am = status_map_am.get(status_val, status_val)
    icon = "⚠️" if status_val == "LATE" else "❌" if status_val == "ABSENT" else "✅" if status_val == "PRESENT" else "ℹ️"

    date_str = date_val.strftime('%Y-%m-%d')
    arr_str_en = arrival_time.strftime('%I:%M %p') if arrival_time else "Not recorded"
    arr_str_am = arrival_time.strftime('%I:%M %p') if arrival_time else "አልተመዘገበም"
    dep_str_en = departure_time.strftime('%I:%M %p') if departure_time else "Not recorded"
    dep_str_am = departure_time.strftime('%I:%M %p') if departure_time else "አልተመዘገበም"

    method_val = method or "Roll Call"
    method_am = translate_method(method_val)

    en = (
        f"{icon} <b>Attendance Status: {status_val}</b>\n"
        f"Student: <b>{student.notification_name}</b> (Code: {student.student_code})\n"
        f"📅 Date: {date_str}\n"
        f"⏰ <b>Arrival Time:</b> {arr_str_en}\n"
        f"⏰ <b>Departure Time:</b> {dep_str_en}\n"
        f"📋 Recorded via: {method_val}"
    )
    am = (
        f"{icon} <b>የመገኘት ሁኔታ: {status_am}</b>\n"
        f"ተማሪ: <b>{student.notification_name}</b> (መለያ: {student.student_code})\n"
        f"📅 ቀን: {date_str}\n"
        f"⏰ <b>የመግቢያ ሰዓት:</b> {arr_str_am}\n"
        f"⏰ <b>የመውጫ ሰዓት:</b> {dep_str_am}\n"
        f"📋 ዘዴ: {method_am}"
    )
    return {"en": en, "am": am}


def enqueue_notifications(db: Session, student: Student, kind: str, message: str | dict[str, str], title: str | dict[str, str] | None = None):
    flag = {
        "ARRIVAL": "arrival_enabled",
        "DEPARTURE": "departure_enabled",
        "LATE": "late_enabled",
        "ABSENCE": "absence_enabled",
        "CLASS_END": "class_end_enabled",
    }.get(kind)

    title_map_am = {
        "ARRIVAL": "የመግቢያ ማሳወቂያ",
        "DEPARTURE": "የመውጫ ማሳወቂያ",
        "LATE": "የማርፈድ ማሳወቂያ",
        "ABSENCE": "የቀሪነት ማሳወቂያ",
        "CLASS_END": "የትምህርት ሰዓት ማጠቃለያ",
        "TEST": "የሙከራ ማሳወቂያ",
    }

    for parent_id in parent_ids_for_student(db, student.id):
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.parent_id == parent_id,
            NotificationSetting.student_id == student.id,
        ).first()

        enabled = True if not setting or not flag else getattr(setting, flag)
        if enabled:
            parent = db.get(User, parent_id)
            lang = (getattr(parent, "language", None) or "en").lower()

            if isinstance(message, dict):
                body = message.get(lang, message.get("en", list(message.values())[0]))
            else:
                body = message

            if isinstance(title, dict):
                notif_title = title.get(lang, title.get("en", f"SchoolGuard: {kind.title()}"))
            elif title:
                notif_title = title
            else:
                if lang == "am":
                    notif_title = f"ስኩልጋርድ: {title_map_am.get(kind, kind)}"
                else:
                    notif_title = f"SchoolGuard: {kind.title()}"

            notif = Notification(
                parent_id=parent_id,
                student_id=student.id,
                type=kind,
                title=notif_title,
                message=body,
                status="PENDING",
            )
            db.add(notif)
            db.flush()

            if parent and parent.telegram_id:
                header = "🔔 <b>የስኩልጋርድ ማሳወቂያ</b>" if lang == "am" else "🔔 <b>SchoolGuard Alert</b>"
                formatted_msg = f"{header}\n\n{body}"
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

    msg_dict = build_arrival_message(student, when, method, is_update=is_update)
    enqueue_notifications(
        db,
        student,
        "ARRIVAL",
        msg_dict,
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

    msg_dict = build_departure_message(student, when, method, a.arrival_time, is_update=is_update)
    enqueue_notifications(
        db,
        student,
        "DEPARTURE",
        msg_dict,
    )

    db.commit()
    db.refresh(a)
    return a
