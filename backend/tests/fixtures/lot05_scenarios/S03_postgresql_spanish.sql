-- SYNTHETIC LAB DATA ONLY: illustrative PostgreSQL-compatible DDL subset, not pg_dump custom format.
CREATE TABLE personas (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100) NOT NULL,
  fecha_nacimiento DATE NOT NULL,
  sexo CHAR(1),
  correo VARCHAR(255),
  comentario TEXT
);
CREATE TABLE citas (
  id SERIAL PRIMARY KEY,
  persona_id INTEGER,
  fecha DATETIME,
  estado VARCHAR(32)
);
INSERT INTO personas VALUES
  (202, 'SYNTHETIC_ONLY_LUCIA', 'SYNTHETIC_ONLY_DEMO', '2000-01-15', 'F', 'ejemplo@example.invalid', 'SYNTHETIC_COMMENT_NEVER_EXPOSE');
