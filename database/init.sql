-- XAMPP / MySQL: run once in phpMyAdmin or mysql CLI before starting the app
CREATE DATABASE IF NOT EXISTS arogyacare
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE arogyacare;

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,
  department VARCHAR(120) NULL,
  date_of_birth DATE NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email (email),
  KEY idx_users_role (role),
  KEY ix_users_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Booking / scheduling (drops legacy shape if migrating: DROP TABLE appointments;)
CREATE TABLE IF NOT EXISTS appointments (
  id INT NOT NULL AUTO_INCREMENT,
  patient_id INT NOT NULL,
  doctor_id INT NOT NULL,
  department VARCHAR(120) NOT NULL,
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  symptoms TEXT NOT NULL,
  emergency TINYINT(1) NOT NULL DEFAULT 0,
  priority_score INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'scheduled',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_appt_date (appointment_date),
  KEY ix_appt_patient_date (patient_id, appointment_date),
  KEY ix_appt_doctor_date (doctor_id, appointment_date),
  KEY ix_appt_priority (priority_score),
  CONSTRAINT fk_appt_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_appt_doctor FOREIGN KEY (doctor_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medical_reports (
  id INT NOT NULL AUTO_INCREMENT,
  patient_id INT NOT NULL,
  title VARCHAR(240) NOT NULL,
  report_type VARCHAR(80) NOT NULL DEFAULT 'laboratory',
  file_path VARCHAR(512) NULL,
  reported_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_report_patient_time (patient_id, reported_at),
  CONSTRAINT fk_report_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prediction_logs (
  id INT NOT NULL AUTO_INCREMENT,
  patient_id INT NOT NULL,
  headline VARCHAR(200) NOT NULL,
  summary TEXT NULL,
  confidence FLOAT NULL,
  category VARCHAR(80) NOT NULL DEFAULT 'general',
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_pred_patient_time (patient_id, created_at),
  CONSTRAINT fk_pred_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- In-app inbox: textual payload is stored in `body` (ORM also exposes alias `message`)
CREATE TABLE IF NOT EXISTS notifications (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(180) NOT NULL,
  body VARCHAR(512) NOT NULL,
  category VARCHAR(64) NOT NULL DEFAULT 'care',
  is_read TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_notif_user_time (user_id, created_at),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS donor_supply (
  id INT NOT NULL AUTO_INCREMENT,
  blood_group VARCHAR(8) NOT NULL,
  units_available INT NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_donor_bg (blood_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS diagnosis_reports (
  id INT NOT NULL AUTO_INCREMENT,
  patient_id INT NOT NULL,
  test_type VARCHAR(64) NOT NULL,
  score INT NOT NULL,
  result VARCHAR(120) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_diag_patient_time (patient_id, created_at),
  KEY ix_diag_type_time (test_type, created_at),
  CONSTRAINT fk_diag_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blood_inventory (
  id INT NOT NULL AUTO_INCREMENT,
  blood_group VARCHAR(8) NOT NULL,
  units_available INT NOT NULL DEFAULT 0,
  last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_blood_inventory_group (blood_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blood_donors (
  id INT NOT NULL AUTO_INCREMENT,
  patient_id INT NOT NULL,
  donor_name VARCHAR(120) NOT NULL,
  age INT NOT NULL,
  gender VARCHAR(20) NOT NULL,
  blood_group VARCHAR(8) NOT NULL,
  phone VARCHAR(32) NOT NULL,
  city VARCHAR(120) NOT NULL,
  donated_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) NOT NULL,
  PRIMARY KEY (id),
  KEY ix_blood_donors_patient (patient_id),
  KEY ix_blood_donors_group (blood_group),
  KEY ix_blood_donors_date (donated_on),
  CONSTRAINT fk_blood_donor_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS feedback (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  message TEXT NOT NULL,
  rating INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_feedback_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
