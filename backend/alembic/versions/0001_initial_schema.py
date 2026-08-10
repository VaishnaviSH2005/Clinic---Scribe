"""Initial schema — full CliniScribe AI database (PRD Chapter 15).

Creates every enum type and table defined in Chapter 15 (Database Design):
hospitals, subscriptions, roles, departments, users, sessions,
password_reset_tokens, patients, medical_profiles, patient_ai_summaries,
documents, timeline_events, appointments, consultations,
consultation_transcripts, ai_entities, soap_notes, clinical_summaries,
ai_recommendations, reports, report_versions, notifications, audit_logs,
settings — with all relationships, cascade rules, and indexes from
Ch15.10/15.11.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-07T18:03:00.875823+00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension per PRD Ch3.5 (enabled but unused for Version 1).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.execute("""CREATE TYPE appointment_status AS ENUM ('upcoming', 'checked_in', 'completed', 'cancelled', 'missed');""")

    op.execute("""CREATE TYPE consultation_status AS ENUM ('draft', 'in_progress', 'ai_processing', 'pending_review', 'approved');""")

    op.execute("""CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');""")

    op.execute("""CREATE TYPE recommendation_type AS ENUM ('possible_diagnosis', 'recommended_test', 'follow_up', 'red_flag');""")

    op.execute("""CREATE TYPE hospital_status AS ENUM ('active', 'inactive', 'suspended');""")

    op.execute("""CREATE TYPE subscription_status AS ENUM ('trial', 'active', 'expired', 'cancelled');""")

    op.execute("""CREATE TYPE role_name AS ENUM ('super_admin', 'hospital_admin', 'doctor', 'receptionist');""")

    op.execute("""CREATE TYPE department_status AS ENUM ('active', 'inactive');""")

    op.execute("""CREATE TYPE gender AS ENUM ('male', 'female', 'other');""")

    op.execute("""CREATE TYPE document_file_type AS ENUM ('pdf', 'jpg', 'png');""")

    op.execute("""CREATE TYPE timeline_event_type AS ENUM ('registration', 'appointment', 'consultation', 'diagnosis', 'uploaded_report', 'follow_up', 'surgery');""")

    op.execute("""CREATE TYPE notification_type AS ENUM ('appointment_reminder', 'consultation_pending', 'ai_processing_complete', 'report_generated', 'system');""")

    op.execute("""CREATE TYPE settings_scope AS ENUM ('hospital', 'user');""")

    op.execute("""CREATE TYPE report_type AS ENUM ('consultation_report', 'soap_report', 'clinical_summary', 'patient_history_report');""")

    op.execute("""CREATE TYPE user_status AS ENUM ('active', 'inactive');""")

    op.execute("""CREATE TABLE hospitals (
	name VARCHAR(255) NOT NULL, 
	registration_number VARCHAR(100) NOT NULL, 
	address_line VARCHAR(255), 
	city VARCHAR(100), 
	state VARCHAR(100), 
	country VARCHAR(100), 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	logo_url VARCHAR(500), 
	status hospital_status NOT NULL, 
	working_hours JSONB, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);""")

    op.execute("""CREATE UNIQUE INDEX ix_hospitals_registration_number ON hospitals (registration_number);""")

    op.execute("""CREATE TABLE roles (
	name role_name NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);""")

    op.execute("""CREATE TABLE departments (
	hospital_id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	head_of_department_id UUID, 
	status department_status NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);""")

    op.execute("""CREATE TABLE users (
	hospital_id UUID, 
	role_id UUID NOT NULL, 
	department_id UUID, 
	full_name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	profile_photo_url VARCHAR(500), 
	employee_id VARCHAR(50), 
	qualification VARCHAR(255), 
	specialization VARCHAR(255), 
	medical_registration_number VARCHAR(100), 
	experience_years SMALLINT, 
	status user_status NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_users_hospital_employee UNIQUE (hospital_id, employee_id)
);""")

    op.execute("""CREATE UNIQUE INDEX ix_users_email ON users (email);""")

    op.execute("""CREATE TABLE subscriptions (
	hospital_id UUID NOT NULL, 
	plan_name VARCHAR(100) NOT NULL, 
	status subscription_status NOT NULL, 
	starts_at DATE NOT NULL, 
	expires_at DATE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
);""")

    op.execute("""CREATE TABLE patients (
	hospital_id UUID NOT NULL, 
	uhid VARCHAR(30) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	date_of_birth DATE NOT NULL, 
	gender gender NOT NULL, 
	blood_group VARCHAR(5), 
	mobile_number VARCHAR(20) NOT NULL, 
	email VARCHAR(255), 
	aadhaar_number VARCHAR(20), 
	emergency_contact_name VARCHAR(255), 
	emergency_contact_number VARCHAR(20), 
	address_line VARCHAR(255), 
	city VARCHAR(100), 
	state VARCHAR(100), 
	country VARCHAR(100), 
	pin_code VARCHAR(10), 
	photo_url VARCHAR(500), 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);""")

    op.execute("""CREATE UNIQUE INDEX ix_patients_uhid ON patients (uhid);""")

    op.execute("""CREATE INDEX ix_patients_hospital_mobile ON patients (hospital_id, mobile_number);""")

    op.execute("""CREATE TABLE notifications (
	user_id UUID NOT NULL, 
	type notification_type NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message TEXT, 
	reference_id UUID, 
	is_read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);""")

    op.execute("""CREATE INDEX ix_notifications_user_read_created ON notifications (user_id, is_read, created_at);""")

    op.execute("""CREATE TABLE audit_logs (
	hospital_id UUID, 
	user_id UUID, 
	action VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100), 
	entity_id UUID, 
	metadata JSONB, 
	ip_address VARCHAR(45), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);""")

    op.execute("""CREATE INDEX ix_audit_logs_hospital_created ON audit_logs (hospital_id, created_at);""")

    op.execute("""CREATE TABLE settings (
	scope settings_scope NOT NULL, 
	hospital_id UUID, 
	user_id UUID, 
	key VARCHAR(100) NOT NULL, 
	value JSONB NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_settings_scope_key UNIQUE (scope, hospital_id, user_id, key), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);""")

    op.execute("""CREATE TABLE sessions (
	user_id UUID NOT NULL, 
	session_token_hash VARCHAR(255) NOT NULL, 
	hospital_id UUID, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);""")

    op.execute("""CREATE TABLE password_reset_tokens (
	user_id UUID NOT NULL, 
	token_hash VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);""")

    op.execute("""CREATE TABLE appointments (
	hospital_id UUID NOT NULL, 
	patient_id UUID NOT NULL, 
	doctor_id UUID NOT NULL, 
	department_id UUID NOT NULL, 
	scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status appointment_status NOT NULL, 
	checked_in_at TIMESTAMP WITH TIME ZONE, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id) ON DELETE RESTRICT, 
	FOREIGN KEY(doctor_id) REFERENCES users (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);""")

    op.execute("""CREATE INDEX ix_appointments_hospital_scheduled ON appointments (hospital_id, scheduled_at);""")

    op.execute("""CREATE INDEX ix_appointments_doctor_scheduled ON appointments (doctor_id, scheduled_at);""")

    op.execute("""CREATE TABLE medical_profiles (
	patient_id UUID NOT NULL, 
	known_allergies JSONB NOT NULL, 
	chronic_diseases JSONB NOT NULL, 
	current_medications JSONB NOT NULL, 
	previous_surgeries JSONB NOT NULL, 
	family_history TEXT, 
	lifestyle_smoking BOOLEAN, 
	lifestyle_alcohol BOOLEAN, 
	lifestyle_tobacco BOOLEAN, 
	height_cm DECIMAL(5, 2), 
	weight_kg DECIMAL(5, 2), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (patient_id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id)
);""")

    op.execute("""CREATE TABLE timeline_events (
	patient_id UUID NOT NULL, 
	event_type timeline_event_type NOT NULL, 
	event_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	reference_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id)
);""")

    op.execute("""CREATE INDEX ix_timeline_events_patient_date ON timeline_events (patient_id, event_date);""")

    op.execute("""CREATE TABLE consultations (
	hospital_id UUID NOT NULL, 
	patient_id UUID NOT NULL, 
	doctor_id UUID NOT NULL, 
	appointment_id UUID, 
	department_id UUID NOT NULL, 
	status consultation_status NOT NULL, 
	chief_complaint TEXT, 
	doctor_notes TEXT, 
	started_at TIMESTAMP WITH TIME ZONE, 
	ended_at TIMESTAMP WITH TIME ZONE, 
	approved_at TIMESTAMP WITH TIME ZONE, 
	approved_by UUID, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id) ON DELETE RESTRICT, 
	FOREIGN KEY(doctor_id) REFERENCES users (id), 
	FOREIGN KEY(appointment_id) REFERENCES appointments (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);""")

    op.execute("""CREATE INDEX ix_consultations_patient_created ON consultations (patient_id, created_at);""")

    op.execute("""CREATE INDEX ix_consultations_doctor_status ON consultations (doctor_id, status);""")

    op.execute("""CREATE TABLE consultation_transcripts (
	consultation_id UUID NOT NULL, 
	raw_transcript JSONB NOT NULL, 
	cleaned_transcript JSONB, 
	audio_file_url VARCHAR(500), 
	audio_duration_seconds INTEGER, 
	stt_provider VARCHAR(50) NOT NULL, 
	manually_edited BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (consultation_id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE CASCADE
);""")

    op.execute("""CREATE TABLE ai_entities (
	consultation_id UUID NOT NULL, 
	symptoms JSONB NOT NULL, 
	medications JSONB NOT NULL, 
	allergies JSONB NOT NULL, 
	medical_history JSONB NOT NULL, 
	vitals JSONB, 
	extraction_confidence confidence_level, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (consultation_id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE CASCADE
);""")

    op.execute("""CREATE TABLE soap_notes (
	consultation_id UUID NOT NULL, 
	subjective TEXT, 
	objective TEXT, 
	assessment TEXT, 
	plan TEXT, 
	ai_generated BOOLEAN NOT NULL, 
	edited_by_doctor BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (consultation_id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE CASCADE
);""")

    op.execute("""CREATE TABLE clinical_summaries (
	consultation_id UUID NOT NULL, 
	chief_complaint TEXT, 
	history_of_present_illness TEXT, 
	key_findings TEXT, 
	assessment TEXT, 
	plan TEXT, 
	word_count SMALLINT, 
	edited_by_doctor BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (consultation_id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE CASCADE
);""")

    op.execute("""CREATE TABLE ai_recommendations (
	consultation_id UUID NOT NULL, 
	type recommendation_type NOT NULL, 
	content TEXT NOT NULL, 
	explanation TEXT, 
	confidence confidence_level, 
	is_red_flag BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE CASCADE
);""")

    op.execute("""CREATE INDEX ix_ai_recommendations_consultation_type ON ai_recommendations (consultation_id, type);""")

    op.execute("""CREATE TABLE patient_ai_summaries (
	patient_id UUID NOT NULL, 
	primary_complaints JSONB NOT NULL, 
	frequently_prescribed_medicines JSONB NOT NULL, 
	significant_diagnoses JSONB NOT NULL, 
	high_risk_alerts JSONB NOT NULL, 
	source_consultation_id UUID, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (patient_id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id), 
	FOREIGN KEY(source_consultation_id) REFERENCES consultations (id)
);""")

    op.execute("""CREATE TABLE documents (
	patient_id UUID NOT NULL, 
	hospital_id UUID NOT NULL, 
	uploaded_by UUID NOT NULL, 
	consultation_id UUID, 
	file_name VARCHAR(255) NOT NULL, 
	file_type document_file_type NOT NULL, 
	file_url VARCHAR(500) NOT NULL, 
	file_size_bytes INTEGER NOT NULL, 
	document_category VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(uploaded_by) REFERENCES users (id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id)
);""")

    op.execute("""CREATE TABLE reports (
	hospital_id UUID NOT NULL, 
	patient_id UUID NOT NULL, 
	consultation_id UUID NOT NULL, 
	report_type report_type NOT NULL, 
	doctor_remarks TEXT, 
	follow_up_date DATE, 
	follow_up_notes TEXT, 
	pdf_url VARCHAR(500), 
	current_version SMALLINT NOT NULL, 
	is_locked BOOLEAN NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id), 
	FOREIGN KEY(consultation_id) REFERENCES consultations (id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);""")

    op.execute("""CREATE INDEX ix_reports_patient_created ON reports (patient_id, created_at);""")

    op.execute("""CREATE TABLE report_versions (
	report_id UUID NOT NULL, 
	version_number SMALLINT NOT NULL, 
	snapshot JSONB NOT NULL, 
	pdf_url VARCHAR(500), 
	created_by UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_report_version UNIQUE (report_id, version_number), 
	FOREIGN KEY(report_id) REFERENCES reports (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);""")

    op.execute("""ALTER TABLE departments ADD FOREIGN KEY(hospital_id) REFERENCES hospitals (id);""")

    op.execute("""ALTER TABLE hospitals ADD FOREIGN KEY(updated_by) REFERENCES users (id);""")

    op.execute("""ALTER TABLE users ADD FOREIGN KEY(department_id) REFERENCES departments (id);""")

    op.execute("""ALTER TABLE departments ADD FOREIGN KEY(created_by) REFERENCES users (id);""")

    op.execute("""ALTER TABLE departments ADD FOREIGN KEY(head_of_department_id) REFERENCES users (id);""")

    op.execute("""ALTER TABLE departments ADD FOREIGN KEY(updated_by) REFERENCES users (id);""")

    op.execute("""ALTER TABLE users ADD FOREIGN KEY(hospital_id) REFERENCES hospitals (id);""")

    op.execute("""ALTER TABLE users ADD FOREIGN KEY(role_id) REFERENCES roles (id);""")

    op.execute("""ALTER TABLE hospitals ADD FOREIGN KEY(created_by) REFERENCES users (id);""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS report_versions CASCADE;")

    op.execute("DROP TABLE IF EXISTS reports CASCADE;")

    op.execute("DROP TABLE IF EXISTS documents CASCADE;")

    op.execute("DROP TABLE IF EXISTS patient_ai_summaries CASCADE;")

    op.execute("DROP TABLE IF EXISTS ai_recommendations CASCADE;")

    op.execute("DROP TABLE IF EXISTS clinical_summaries CASCADE;")

    op.execute("DROP TABLE IF EXISTS soap_notes CASCADE;")

    op.execute("DROP TABLE IF EXISTS ai_entities CASCADE;")

    op.execute("DROP TABLE IF EXISTS consultation_transcripts CASCADE;")

    op.execute("DROP TABLE IF EXISTS consultations CASCADE;")

    op.execute("DROP TABLE IF EXISTS timeline_events CASCADE;")

    op.execute("DROP TABLE IF EXISTS medical_profiles CASCADE;")

    op.execute("DROP TABLE IF EXISTS appointments CASCADE;")

    op.execute("DROP TABLE IF EXISTS password_reset_tokens CASCADE;")

    op.execute("DROP TABLE IF EXISTS sessions CASCADE;")

    op.execute("DROP TABLE IF EXISTS settings CASCADE;")

    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")

    op.execute("DROP TABLE IF EXISTS notifications CASCADE;")

    op.execute("DROP TABLE IF EXISTS patients CASCADE;")

    op.execute("DROP TABLE IF EXISTS subscriptions CASCADE;")

    op.execute("DROP TABLE IF EXISTS users CASCADE;")

    op.execute("DROP TABLE IF EXISTS departments CASCADE;")

    op.execute("DROP TABLE IF EXISTS roles CASCADE;")

    op.execute("DROP TABLE IF EXISTS hospitals CASCADE;")

    op.execute("DROP TYPE IF EXISTS user_status;")

    op.execute("DROP TYPE IF EXISTS report_type;")

    op.execute("DROP TYPE IF EXISTS settings_scope;")

    op.execute("DROP TYPE IF EXISTS notification_type;")

    op.execute("DROP TYPE IF EXISTS timeline_event_type;")

    op.execute("DROP TYPE IF EXISTS document_file_type;")

    op.execute("DROP TYPE IF EXISTS gender;")

    op.execute("DROP TYPE IF EXISTS department_status;")

    op.execute("DROP TYPE IF EXISTS role_name;")

    op.execute("DROP TYPE IF EXISTS subscription_status;")

    op.execute("DROP TYPE IF EXISTS hospital_status;")

    op.execute("DROP TYPE IF EXISTS recommendation_type;")

    op.execute("DROP TYPE IF EXISTS confidence_level;")

    op.execute("DROP TYPE IF EXISTS consultation_status;")

    op.execute("DROP TYPE IF EXISTS appointment_status;")

