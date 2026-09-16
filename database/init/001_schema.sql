CREATE DATABASE IF NOT EXISTS schoolguard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE schoolguard;

CREATE TABLE schools (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  code VARCHAR(50) NOT NULL UNIQUE,
  address VARCHAR(300) NULL,
  phone VARCHAR(50) NULL,
  timezone VARCHAR(80) NOT NULL DEFAULT 'Africa/Addis_Ababa',
  school_start_time TIME NULL,
  school_end_time TIME NULL,
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  school_id BIGINT UNSIGNED NULL,
  telegram_id BIGINT NULL UNIQUE,
  telegram_username VARCHAR(100) NULL,
  full_name VARCHAR(200) NOT NULL,
  email VARCHAR(200) NULL UNIQUE,
  phone VARCHAR(50) NULL,
  password_hash VARCHAR(255) NULL,
  role ENUM('ADMIN','TEACHER','PARENT','SECURITY') NOT NULL,
  status ENUM('ACTIVE','INACTIVE','PENDING') NOT NULL DEFAULT 'ACTIVE',
  language VARCHAR(10) NOT NULL DEFAULT 'en',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_school FOREIGN KEY (school_id) REFERENCES schools(id)
) ENGINE=InnoDB;

CREATE TABLE classes (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  school_id BIGINT UNSIGNED NOT NULL,
  class_code VARCHAR(50) NOT NULL,
  class_name VARCHAR(100) NOT NULL,
  grade VARCHAR(50) NOT NULL,
  section VARCHAR(50) NULL,
  academic_year VARCHAR(50) NOT NULL,
  school_start_time TIME NULL,
  school_end_time TIME NULL,
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_class_code_school (school_id, class_code),
  CONSTRAINT fk_classes_school FOREIGN KEY (school_id) REFERENCES schools(id)
) ENGINE=InnoDB;

CREATE TABLE students (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  school_id BIGINT UNSIGNED NOT NULL,
  class_id BIGINT UNSIGNED NULL,
  student_code VARCHAR(50) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100) NULL,
  last_name VARCHAR(100) NULL,
  gender VARCHAR(20) NULL,
  date_of_birth DATE NULL,
  qr_token VARCHAR(255) NULL UNIQUE,
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_student_code_school (school_id, student_code),
  INDEX idx_students_class (class_id),
  CONSTRAINT fk_students_school FOREIGN KEY (school_id) REFERENCES schools(id),
  CONSTRAINT fk_students_class FOREIGN KEY (class_id) REFERENCES classes(id)
) ENGINE=InnoDB;

CREATE TABLE parent_students (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  parent_id BIGINT UNSIGNED NOT NULL,
  student_id BIGINT UNSIGNED NOT NULL,
  relationship_type VARCHAR(50) NOT NULL DEFAULT 'PARENT',
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_parent_student (parent_id, student_id),
  CONSTRAINT fk_parent_students_parent FOREIGN KEY (parent_id) REFERENCES users(id),
  CONSTRAINT fk_parent_students_student FOREIGN KEY (student_id) REFERENCES students(id)
) ENGINE=InnoDB;

CREATE TABLE teacher_classes (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  teacher_id BIGINT UNSIGNED NOT NULL,
  class_id BIGINT UNSIGNED NOT NULL,
  academic_year VARCHAR(50) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_teacher_class (teacher_id, class_id, academic_year),
  CONSTRAINT fk_teacher_classes_teacher FOREIGN KEY (teacher_id) REFERENCES users(id),
  CONSTRAINT fk_teacher_classes_class FOREIGN KEY (class_id) REFERENCES classes(id)
) ENGINE=InnoDB;

CREATE TABLE attendance (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  student_id BIGINT UNSIGNED NOT NULL,
  attendance_date DATE NOT NULL,
  arrival_time DATETIME NULL,
  departure_time DATETIME NULL,
  status ENUM('PRESENT','ABSENT','LATE','EXCUSED') NOT NULL DEFAULT 'PRESENT',
  arrival_method ENUM('QR','TEACHER','SECURITY','RFID','MANUAL') NULL,
  departure_method ENUM('QR','TEACHER','SECURITY','RFID','MANUAL') NULL,
  recorded_by BIGINT UNSIGNED NULL,
  notes VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_student_attendance_date (student_id, attendance_date),
  INDEX idx_attendance_date (attendance_date),
  CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES students(id),
  CONSTRAINT fk_attendance_recorder FOREIGN KEY (recorded_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE attendance_events (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  student_id BIGINT UNSIGNED NOT NULL,
  event_type ENUM('ARRIVAL','DEPARTURE','STATUS_CHANGE') NOT NULL,
  event_time DATETIME NOT NULL,
  method VARCHAR(50) NULL,
  recorded_by BIGINT UNSIGNED NULL,
  notes VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_event_student_time (student_id, event_time),
  CONSTRAINT fk_events_student FOREIGN KEY (student_id) REFERENCES students(id),
  CONSTRAINT fk_events_recorder FOREIGN KEY (recorded_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE class_schedules (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  class_id BIGINT UNSIGNED NOT NULL,
  teacher_id BIGINT UNSIGNED NULL,
  day_of_week TINYINT NOT NULL,
  subject VARCHAR(100) NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  CONSTRAINT fk_schedule_class FOREIGN KEY (class_id) REFERENCES classes(id),
  CONSTRAINT fk_schedule_teacher FOREIGN KEY (teacher_id) REFERENCES users(id),
  INDEX idx_schedule_day (class_id, day_of_week)
) ENGINE=InnoDB;

CREATE TABLE notification_settings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  parent_id BIGINT UNSIGNED NOT NULL,
  student_id BIGINT UNSIGNED NOT NULL,
  arrival_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  departure_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  late_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  absence_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  class_end_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_notification_parent_student (parent_id, student_id),
  CONSTRAINT fk_notification_parent FOREIGN KEY (parent_id) REFERENCES users(id),
  CONSTRAINT fk_notification_student FOREIGN KEY (student_id) REFERENCES students(id)
) ENGINE=InnoDB;

CREATE TABLE notifications (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  parent_id BIGINT UNSIGNED NOT NULL,
  student_id BIGINT UNSIGNED NULL,
  type ENUM('ARRIVAL','DEPARTURE','LATE','ABSENCE','CLASS_END','SYSTEM') NOT NULL,
  channel ENUM('TELEGRAM','EMAIL','SMS') NOT NULL DEFAULT 'TELEGRAM',
  title VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  status ENUM('PENDING','SENT','FAILED') NOT NULL DEFAULT 'PENDING',
  sent_at DATETIME NULL,
  error_message VARCHAR(1000) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notifications_parent FOREIGN KEY (parent_id) REFERENCES users(id),
  CONSTRAINT fk_notifications_student FOREIGN KEY (student_id) REFERENCES students(id),
  INDEX idx_notifications_status (status, created_at)
) ENGINE=InnoDB;

CREATE TABLE registration_codes (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  school_id BIGINT UNSIGNED NOT NULL,
  code VARCHAR(100) NOT NULL UNIQUE,
  role ENUM('PARENT','TEACHER','SECURITY') NOT NULL,
  student_id BIGINT UNSIGNED NULL,
  expires_at DATETIME NULL,
  used_at DATETIME NULL,
  created_by BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reg_school FOREIGN KEY (school_id) REFERENCES schools(id),
  CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES students(id),
  CONSTRAINT fk_reg_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE audit_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  school_id BIGINT UNSIGNED NULL,
  actor_user_id BIGINT UNSIGNED NULL,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id BIGINT UNSIGNED NULL,
  old_value JSON NULL,
  new_value JSON NULL,
  ip_address VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_entity (entity_type, entity_id),
  INDEX idx_audit_created (created_at),
  CONSTRAINT fk_audit_school FOREIGN KEY (school_id) REFERENCES schools(id),
  CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

INSERT INTO schools
(name, code, address, timezone, school_start_time, school_end_time)
VALUES
('SchoolGuard Demo School', 'DEMO', 'Addis Ababa, Ethiopia',
 'Africa/Addis_Ababa', '08:00:00', '16:00:00');
