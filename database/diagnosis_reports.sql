-- Run in MySQL/phpMyAdmin if you manage schema manually ( complements SQLAlchemy create_all )
USE arogyacare;

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
