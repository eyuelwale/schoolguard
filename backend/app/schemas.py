from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    password: str
    role: str = "PARENT"


class UserLogin(BaseModel):
    email: str  # Supports email address, username, or phone number
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    role: str
    telegram_id: int | None
    telegram_username: str | None
    status: str
    language: str | None = "en"
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClassCreate(BaseModel):
    school_id: int
    class_code: str
    class_name: str
    grade: str
    section: str | None = None
    academic_year: str
    school_start_time: time | None = None
    school_end_time: time | None = None


class ClassOut(ClassCreate):
    id: int
    status: str
    model_config = ConfigDict(from_attributes=True)


class StudentCreate(BaseModel):
    school_id: int
    class_id: int | None = None
    student_code: str
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None


class StudentOut(StudentCreate):
    id: int
    qr_token: str | None
    status: str
    model_config = ConfigDict(from_attributes=True)


class LinkStudent(BaseModel):
    parent_id: int
    student_id: int
    relationship_type: str = "PARENT"
    is_primary: bool = False


class AssignTeacher(BaseModel):
    teacher_id: int
    class_id: int
    academic_year: str


class AttendanceArrival(BaseModel):
    student_id: int
    method: str = "TEACHER"
    arrival_time: datetime | None = None


class AttendanceDeparture(BaseModel):
    student_id: int
    method: str = "TEACHER"
    departure_time: datetime | None = None


class AttendanceStatus(BaseModel):
    student_id: int
    status: str


class BulkAttendanceIn(BaseModel):
    student_ids: list[int]
    attendance_date: date
    event_type: str = "ARRIVAL"   # "ARRIVAL", "DEPARTURE", or "STATUS"
    method: str = "TEACHER"
    event_time: datetime | None = None  # if None, defaults to now()
    status: str | None = None          # required when event_type == "STATUS"




class AttendanceOut(BaseModel):
    id: int
    student_id: int
    attendance_date: date
    arrival_time: datetime | None
    departure_time: datetime | None
    status: str
    arrival_method: str | None
    departure_method: str | None
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    status: str | None = None
    password: str | None = None
    telegram_id: int | None = None
    telegram_username: str | None = None

    @field_validator("email", "phone", "telegram_username", mode="before")
    @classmethod
    def empty_user_fields_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class SchoolCreate(BaseModel):
    name: str
    code: str
    address: str | None = None
    phone: str | None = None


class SchoolUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    address: str | None = None
    phone: str | None = None
    status: str | None = None

    @field_validator("address", "phone", mode="before")
    @classmethod
    def empty_school_fields_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class SchoolOut(SchoolCreate):
    id: int
    status: str
    model_config = ConfigDict(from_attributes=True)


class ClassUpdate(BaseModel):
    school_id: int | None = None
    class_code: str | None = None
    class_name: str | None = None
    grade: str | None = None
    section: str | None = None
    academic_year: str | None = None
    school_start_time: time | None = None
    school_end_time: time | None = None
    status: str | None = None

    @field_validator("section", "school_start_time", "school_end_time", mode="before")
    @classmethod
    def empty_class_fields_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class StudentUpdate(BaseModel):
    school_id: int | None = None
    class_id: int | None = None
    student_code: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    status: str | None = None

    @field_validator("class_id", "middle_name", "last_name", "date_of_birth", mode="before")
    @classmethod
    def empty_student_fields_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class ParentLinkOut(BaseModel):
    id: int
    parent_id: int
    student_id: int
    parent_name: str
    parent_email: str | None = None
    parent_phone: str | None = None
    student_name: str
    student_code: str
    relationship_type: str
    is_primary: bool


class ParentLinkUpdate(BaseModel):
    relationship_type: str | None = None
    is_primary: bool | None = None


class AttendanceUpdate(BaseModel):
    status: str | None = None
    arrival_time: datetime | None = None
    departure_time: datetime | None = None
    arrival_method: str | None = None
    departure_method: str | None = None
    notes: str | None = None

    @field_validator("arrival_time", "departure_time", "arrival_method", "departure_method", "notes", mode="before")
    @classmethod
    def empty_att_fields_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class ScheduleCreate(BaseModel):
    class_id: int
    teacher_id: int | None = None
    day_of_week: int
    subject: str
    start_time: time
    end_time: time


class NotificationSettingsIn(BaseModel):
    student_id: int
    arrival_enabled: bool = True
    departure_enabled: bool = True
    late_enabled: bool = True
    absence_enabled: bool = True
    class_end_enabled: bool = True


class TelegramLinkIn(BaseModel):
    telegram_id: int
    telegram_username: str | None = None
    language: str | None = None


class BulkDeleteIn(BaseModel):
    ids: list[int]

