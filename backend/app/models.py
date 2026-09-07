from datetime import datetime, date, time
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class School(Base):
    __tablename__ = "schools"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    address: Mapped[str | None] = mapped_column(String(300))
    phone: Mapped[str | None] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(80), default="Africa/Addis_Ababa")
    school_start_time: Mapped[time | None] = mapped_column(Time)
    school_end_time: Mapped[time | None] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id"))
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    school = relationship("School")


class ClassRoom(Base):
    __tablename__ = "classes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    class_code: Mapped[str] = mapped_column(String(50))
    class_name: Mapped[str] = mapped_column(String(100))
    grade: Mapped[str] = mapped_column(String(50))
    section: Mapped[str | None] = mapped_column(String(50))
    academic_year: Mapped[str] = mapped_column(String(50))
    school_start_time: Mapped[time | None] = mapped_column(Time)
    school_end_time: Mapped[time | None] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"))
    student_code: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    qr_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    classroom = relationship("ClassRoom")

    @property
    def notification_name(self) -> str:
        second_name = self.middle_name if self.middle_name else (self.last_name or "")
        return f"{self.first_name} {second_name}".strip()



class ParentStudent(Base):
    __tablename__ = "parent_students"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    relationship_type: Mapped[str] = mapped_column(String(50), default="PARENT")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    parent = relationship("User")
    student = relationship("Student")
    __table_args__ = (UniqueConstraint("parent_id", "student_id"),)


class TeacherClass(Base):
    __tablename__ = "teacher_classes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    academic_year: Mapped[str] = mapped_column(String(50))
    teacher = relationship("User")
    classroom = relationship("ClassRoom")
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", "academic_year"),)


class Attendance(Base):
    __tablename__ = "attendance"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    attendance_date: Mapped[date] = mapped_column(Date)
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="PRESENT")
    arrival_method: Mapped[str | None] = mapped_column(String(50))
    departure_method: Mapped[str | None] = mapped_column(String(50))
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(String(500))
    student = relationship("Student")
    recorder = relationship("User")
    __table_args__ = (UniqueConstraint("student_id", "attendance_date"),)


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    event_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    method: Mapped[str | None] = mapped_column(String(50))
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(String(500))
    student = relationship("Student")


class ClassSchedule(Base):
    __tablename__ = "class_schedules"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    arrival_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    departure_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    late_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    absence_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    class_end_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("parent_id", "student_id"),)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    type: Mapped[str] = mapped_column(String(30))
    channel: Mapped[str] = mapped_column(String(30), default="TELEGRAM")
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RegistrationCode(Base):
    __tablename__ = "registration_codes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    code: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(30))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id"))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
