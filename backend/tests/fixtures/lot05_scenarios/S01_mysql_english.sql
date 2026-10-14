-- SYNTHETIC LAB DATA ONLY: not a customer export; DDL inspection must NEVER execute INSERT statements.
CREATE TABLE legacy_patients (
  patient_id INTEGER PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  birth_date DATE NOT NULL,
  sex CHAR(1),
  email VARCHAR(255),
  password_hash VARCHAR(255),
  legacy_notes TEXT
);
CREATE TABLE legacy_appointments (
  appointment_id INTEGER PRIMARY KEY,
  patient_ref INTEGER,
  scheduled_at DATETIME,
  status VARCHAR(30)
);
INSERT INTO legacy_patients VALUES
  (101, 'SYNTHETIC_ONLY_ALICE', 'SYNTHETIC_ONLY_EXAMPLE', '1999-05-04', 'F', 'fake@example.invalid', 'FAKE_SECRET_NEVER_IMPORT', 'SYNTHETIC_NOTE_DO_NOT_EXPOSE');
