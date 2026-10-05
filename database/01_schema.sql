-- =====================================================================
-- Sistema de Tickets de Soporte TI - Esquema de la base de datos
-- Motor: MySQL 8 / MariaDB 10.5+ (InnoDB)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS soporte_ti
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE soporte_ti;

-- Se eliminan en orden inverso a las dependencias (permite re-crear la BD)
DROP TABLE IF EXISTS historial_tickets;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS tecnico_especialidad;
DROP TABLE IF EXISTS perfiles_tecnico;
DROP TABLE IF EXISTS tecnicos;
DROP TABLE IF EXISTS especialidades;
DROP TABLE IF EXISTS usuarios_ti;
DROP TABLE IF EXISTS departamentos;

-- ---------------------------------------------------------------------
-- departamentos  (1) ---< (N) usuarios
-- ---------------------------------------------------------------------
CREATE TABLE departamentos (
    id_departamento INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL UNIQUE,
    ubicacion       VARCHAR(80) NULL,
    CONSTRAINT chk_departamento_nombre CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3)
) ENGINE=InnoDB;

CREATE TABLE usuarios_ti (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    id_departamento INT NOT NULL,
    activo          TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_usuario_nombre CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3),
    CONSTRAINT chk_usuario_email  CHECK (email LIKE '%_@_%.__%'),
    CONSTRAINT fk_usuario_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamentos (id_departamento)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- tecnicos (1) ---- (1) perfiles_tecnico        -> relación 1:1
-- La PK de perfiles_tecnico es a la vez FK hacia tecnicos.
-- ---------------------------------------------------------------------
CREATE TABLE tecnicos (
    id_tecnico INT AUTO_INCREMENT PRIMARY KEY,
    nombre     VARCHAR(100) NOT NULL,
    email      VARCHAR(120) NOT NULL UNIQUE,
    activo     TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_tecnico_nombre CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3),
    CONSTRAINT chk_tecnico_email  CHECK (email LIKE '%_@_%.__%')
) ENGINE=InnoDB;

CREATE TABLE perfiles_tecnico (
    id_tecnico        INT PRIMARY KEY,
    telefono          VARCHAR(20) NULL,
    turno             ENUM('Mañana','Tarde','Noche') NOT NULL DEFAULT 'Mañana',
    nivel             ENUM('Junior','Semi Senior','Senior') NOT NULL DEFAULT 'Junior',
    anios_experiencia TINYINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT chk_perfil_experiencia CHECK (anios_experiencia <= 50),
    CONSTRAINT fk_perfil_tecnico FOREIGN KEY (id_tecnico)
        REFERENCES tecnicos (id_tecnico)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- tecnicos (N) ---< tecnico_especialidad >--- (M) especialidades   -> N:M
-- La tabla intermedia tiene PK compuesta (evita duplicados).
-- ---------------------------------------------------------------------
CREATE TABLE especialidades (
    id_especialidad INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL UNIQUE,
    descripcion     VARCHAR(200) NULL,
    CONSTRAINT chk_especialidad_nombre CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3)
) ENGINE=InnoDB;

CREATE TABLE tecnico_especialidad (
    id_tecnico      INT NOT NULL,
    id_especialidad INT NOT NULL,
    PRIMARY KEY (id_tecnico, id_especialidad),
    CONSTRAINT fk_te_tecnico FOREIGN KEY (id_tecnico)
        REFERENCES tecnicos (id_tecnico)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_te_especialidad FOREIGN KEY (id_especialidad)
        REFERENCES especialidades (id_especialidad)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- tickets: un usuario crea muchos tickets (1:N), un técnico atiende
-- muchos tickets (1:N) y cada ticket pertenece a una especialidad (1:N).
-- ---------------------------------------------------------------------
CREATE TABLE tickets (
    id_ticket       INT AUTO_INCREMENT PRIMARY KEY,
    titulo          VARCHAR(120) NOT NULL,
    descripcion     TEXT NOT NULL,
    prioridad       ENUM('Baja','Media','Alta','Crítica') NOT NULL DEFAULT 'Media',
    estado          ENUM('Abierto','En proceso','Resuelto','Cerrado') NOT NULL DEFAULT 'Abierto',
    id_usuario      INT NOT NULL,
    id_tecnico      INT NULL,
    id_especialidad INT NOT NULL,
    fecha_creacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre    DATETIME NULL,
    CONSTRAINT chk_ticket_titulo CHECK (CHAR_LENGTH(TRIM(titulo)) >= 5),
    CONSTRAINT chk_ticket_descripcion CHECK (CHAR_LENGTH(TRIM(descripcion)) >= 10),
    -- Regla: sin técnico asignado el ticket solo puede estar Abierto
    CONSTRAINT chk_ticket_estado_tecnico CHECK (estado = 'Abierto' OR id_tecnico IS NOT NULL),
    -- Regla: fecha_cierre existe si y solo si el ticket está Resuelto o Cerrado
    CONSTRAINT chk_ticket_fecha_cierre CHECK ((estado IN ('Resuelto','Cerrado')) = (fecha_cierre IS NOT NULL)),
    CONSTRAINT fk_ticket_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios_ti (id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_tecnico FOREIGN KEY (id_tecnico)
        REFERENCES tecnicos (id_tecnico)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_especialidad FOREIGN KEY (id_especialidad)
        REFERENCES especialidades (id_especialidad)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_ticket_estado (estado),
    INDEX idx_ticket_prioridad (prioridad)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- historial_tickets: bitácora que llenan los procedimientos almacenados.
-- ---------------------------------------------------------------------
CREATE TABLE historial_tickets (
    id_historial    INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket       INT NOT NULL,
    accion          VARCHAR(200) NOT NULL,
    estado_anterior VARCHAR(20) NULL,
    estado_nuevo    VARCHAR(20) NULL,
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historial_ticket FOREIGN KEY (id_ticket)
        REFERENCES tickets (id_ticket)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;
