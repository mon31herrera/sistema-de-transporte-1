CREATE DATABASE IF NOT EXISTS transporte_escolar
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE transporte_escolar;

CREATE TABLE IF NOT EXISTS rutas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  origen VARCHAR(150) NOT NULL,
  destino VARCHAR(150) NOT NULL,
  descripcion VARCHAR(255),
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS horarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ruta_id INT NOT NULL,
  hora_salida TIME NOT NULL,
  hora_llegada TIME NOT NULL,
  cupos_totales INT NOT NULL,
  cupos_disponibles INT NOT NULL,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_horarios_rutas
    FOREIGN KEY (ruta_id) REFERENCES rutas(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_cupos_totales CHECK (cupos_totales > 0),
  CONSTRAINT chk_cupos_disponibles CHECK (cupos_disponibles >= 0)
);

CREATE TABLE IF NOT EXISTS reservas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  horario_id INT NOT NULL,
  estudiante VARCHAR(120) NOT NULL,
  acudiente VARCHAR(120) NOT NULL,
  telefono VARCHAR(30) NOT NULL,
  fecha_reserva DATE NOT NULL,
  estado ENUM('Activa', 'Cancelada') NOT NULL DEFAULT 'Activa',
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reservas_horarios
    FOREIGN KEY (horario_id) REFERENCES horarios(id)
    ON DELETE CASCADE
);

INSERT INTO rutas (nombre, origen, destino, descripcion)
SELECT 'Ruta Norte', 'Colegio Central', 'Barrio Los Pinos', 'Pasa por la avenida principal'
WHERE NOT EXISTS (SELECT 1 FROM rutas WHERE nombre = 'Ruta Norte');

INSERT INTO rutas (nombre, origen, destino, descripcion)
SELECT 'Ruta Sur', 'Colegio Central', 'Urbanizacion El Lago', 'Servicio de tarde'
WHERE NOT EXISTS (SELECT 1 FROM rutas WHERE nombre = 'Ruta Sur');
