from backend.app.database import engine, Base
# Import all models so SQLAlchemy registers them with Base.metadata
from backend.app.models import (
    School, User, ClassRoom, Student, ParentStudent,
    Attendance, AttendanceEvent, Notification, NotificationSetting,
    RegistrationCode
)

def init_database():
    """Create all tables defined in models.py in the target database (MySQL or Supabase PostgreSQL)."""
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables successfully initialized!")

if __name__ == "__main__":
    init_database()
