-- ==============================================================================
-- SchoolGuard — Supabase (PostgreSQL) Initial Schema
-- Run this in the Supabase SQL Editor to create all tables and indexes.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS schools (
	id BIGSERIAL NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	address VARCHAR(300), 
	phone VARCHAR(50), 
	timezone VARCHAR(80) NOT NULL DEFAULT 'Africa/Addis_Ababa', 
	school_start_time TIME WITHOUT TIME ZONE, 
	school_end_time TIME WITHOUT TIME ZONE, 
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS classes (
	id BIGSERIAL NOT NULL, 
	school_id BIGINT NOT NULL, 
	class_code VARCHAR(50) NOT NULL, 
	class_name VARCHAR(100) NOT NULL, 
	grade VARCHAR(50) NOT NULL, 
	section VARCHAR(50), 
	academic_year VARCHAR(50) NOT NULL, 
	school_start_time TIME WITHOUT TIME ZONE, 
	school_end_time TIME WITHOUT TIME ZONE, 
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
	id BIGSERIAL NOT NULL, 
	school_id BIGINT, 
	telegram_id BIGINT, 
	telegram_username VARCHAR(100), 
	full_name VARCHAR(200) NOT NULL, 
	email VARCHAR(200), 
	phone VARCHAR(50), 
	password_hash VARCHAR(255), 
	role VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE SET NULL, 
	UNIQUE (telegram_id), 
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS audit_logs (
	id BIGSERIAL NOT NULL, 
	school_id BIGINT, 
	actor_user_id BIGINT, 
	action VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100) NOT NULL, 
	entity_id BIGINT, 
	old_value TEXT, 
	new_value TEXT, 
	ip_address VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE SET NULL, 
	FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS class_schedules (
	id BIGSERIAL NOT NULL, 
	class_id BIGINT NOT NULL, 
	teacher_id BIGINT, 
	day_of_week INTEGER NOT NULL, 
	subject VARCHAR(100) NOT NULL, 
	start_time TIME WITHOUT TIME ZONE NOT NULL, 
	end_time TIME WITHOUT TIME ZONE NOT NULL, 
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', 
	PRIMARY KEY (id), 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
	FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS students (
	id BIGSERIAL NOT NULL, 
	school_id BIGINT NOT NULL, 
	class_id BIGINT, 
	student_code VARCHAR(50) NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	middle_name VARCHAR(100), 
	last_name VARCHAR(100), 
	gender VARCHAR(20), 
	date_of_birth DATE, 
	qr_token VARCHAR(255), 
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE SET NULL, 
	UNIQUE (qr_token)
);

CREATE TABLE IF NOT EXISTS teacher_classes (
	id BIGSERIAL NOT NULL, 
	teacher_id BIGINT NOT NULL, 
	class_id BIGINT NOT NULL, 
	academic_year VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (teacher_id, class_id, academic_year), 
	FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
	id BIGSERIAL NOT NULL, 
	student_id BIGINT NOT NULL, 
	attendance_date DATE NOT NULL, 
	arrival_time TIMESTAMP WITHOUT TIME ZONE, 
	departure_time TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(30) NOT NULL, 
	arrival_method VARCHAR(50), 
	departure_method VARCHAR(50), 
	recorded_by BIGINT, 
	notes VARCHAR(500), 
	PRIMARY KEY (id), 
	UNIQUE (student_id, attendance_date), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(recorded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS attendance_events (
	id BIGSERIAL NOT NULL, 
	student_id BIGINT NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	event_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	method VARCHAR(50), 
	recorded_by BIGINT, 
	notes VARCHAR(500), 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(recorded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notification_settings (
	id BIGSERIAL NOT NULL, 
	parent_id BIGINT NOT NULL, 
	student_id BIGINT NOT NULL, 
	arrival_enabled BOOLEAN NOT NULL DEFAULT TRUE, 
	departure_enabled BOOLEAN NOT NULL DEFAULT TRUE, 
	late_enabled BOOLEAN NOT NULL DEFAULT TRUE, 
	absence_enabled BOOLEAN NOT NULL DEFAULT TRUE, 
	class_end_enabled BOOLEAN NOT NULL DEFAULT TRUE, 
	PRIMARY KEY (id), 
	UNIQUE (parent_id, student_id), 
	FOREIGN KEY(parent_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
	id BIGSERIAL NOT NULL, 
	parent_id BIGINT NOT NULL, 
	student_id BIGINT, 
	type VARCHAR(30) NOT NULL, 
	channel VARCHAR(30) NOT NULL DEFAULT 'TELEGRAM', 
	title VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL DEFAULT 'PENDING', 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	error_message VARCHAR(1000), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS parent_students (
	id BIGSERIAL NOT NULL, 
	parent_id BIGINT NOT NULL, 
	student_id BIGINT NOT NULL, 
	relationship_type VARCHAR(50) NOT NULL DEFAULT 'PARENT', 
	is_primary BOOLEAN NOT NULL DEFAULT FALSE, 
	PRIMARY KEY (id), 
	UNIQUE (parent_id, student_id), 
	FOREIGN KEY(parent_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS registration_codes (
	id BIGSERIAL NOT NULL, 
	school_id BIGINT NOT NULL, 
	code VARCHAR(100) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	student_id BIGINT, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	used_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	UNIQUE (code), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
);
