-- =====================================================================
-- PROCEDIMIENTOS ALMACENADOS del sistema de tickets
-- (No se usan triggers: en el servidor del colegio no hay permiso SUPER.)
-- Toda la lógica del ciclo de vida del ticket y su historial vive aquí:
--   sp_crear_ticket    -> crea el ticket y deja el registro en el historial
--   sp_asignar_ticket  -> asigna técnico validando reglas y registra historial
--   sp_cambiar_estado  -> cambia el estado respetando el ciclo de vida
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_crear_ticket;
DROP PROCEDURE IF EXISTS sp_asignar_ticket;
DROP PROCEDURE IF EXISTS sp_cambiar_estado;

DELIMITER $$

-- ---------------------------------------------------------------------
-- sp_crear_ticket: solo usuarios activos pueden crear tickets.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_crear_ticket(
    IN p_titulo VARCHAR(120), IN p_descripcion TEXT, IN p_prioridad VARCHAR(10),
    IN p_id_usuario INT, IN p_id_especialidad INT)
BEGIN
    DECLARE v_activo TINYINT;
    DECLARE v_id INT;

    IF NOT EXISTS (SELECT 1 FROM usuarios_ti WHERE id_usuario = p_id_usuario) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario indicado no existe';
    END IF;

    SELECT activo INTO v_activo FROM usuarios_ti WHERE id_usuario = p_id_usuario;
    IF v_activo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un usuario inactivo no puede crear tickets';
    END IF;

    INSERT INTO tickets (titulo, descripcion, prioridad, id_usuario, id_especialidad)
    VALUES (p_titulo, p_descripcion, p_prioridad, p_id_usuario, p_id_especialidad);
    SET v_id = LAST_INSERT_ID();

    INSERT INTO historial_tickets (id_ticket, accion, estado_anterior, estado_nuevo)
    VALUES (v_id, 'Ticket creado', NULL, 'Abierto');

    SELECT v_id AS id_ticket;
END$$

-- ---------------------------------------------------------------------
-- sp_asignar_ticket: reglas de asignación
--   * ticket y técnico existen; ticket no Resuelto/Cerrado
--   * técnico activo, con la especialidad del ticket (N:M) y < 5 en proceso
-- Deja el ticket En proceso y registra el historial.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_asignar_ticket(IN p_id_ticket INT, IN p_id_tecnico INT)
BEGIN
    DECLARE v_estado          VARCHAR(20);
    DECLARE v_especialidad    INT;
    DECLARE v_tecnico_actual  INT;
    DECLARE v_activo          TINYINT;
    DECLARE v_nombre          VARCHAR(100);
    DECLARE v_tiene_esp       INT;
    DECLARE v_carga           INT;

    IF NOT EXISTS (SELECT 1 FROM tickets WHERE id_ticket = p_id_ticket) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El ticket indicado no existe';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM tecnicos WHERE id_tecnico = p_id_tecnico) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El técnico indicado no existe';
    END IF;

    SELECT estado, id_especialidad, id_tecnico
      INTO v_estado, v_especialidad, v_tecnico_actual
      FROM tickets WHERE id_ticket = p_id_ticket;

    SELECT activo, nombre INTO v_activo, v_nombre
      FROM tecnicos WHERE id_tecnico = p_id_tecnico;

    IF v_estado IN ('Resuelto', 'Cerrado') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No se puede asignar un ticket resuelto o cerrado';
    END IF;

    IF v_activo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El técnico está inactivo';
    END IF;

    SELECT COUNT(*) INTO v_tiene_esp
      FROM tecnico_especialidad
     WHERE id_tecnico = p_id_tecnico AND id_especialidad = v_especialidad;

    IF v_tiene_esp = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El técnico no tiene la especialidad que requiere el ticket';
    END IF;

    SELECT COUNT(*) INTO v_carga
      FROM tickets
     WHERE id_tecnico = p_id_tecnico AND estado = 'En proceso' AND id_ticket <> p_id_ticket;

    IF v_carga >= 5 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El técnico ya tiene 5 tickets en proceso (carga máxima)';
    END IF;

    UPDATE tickets
       SET id_tecnico = p_id_tecnico, estado = 'En proceso'
     WHERE id_ticket = p_id_ticket;

    IF NOT (v_tecnico_actual <=> p_id_tecnico) THEN
        INSERT INTO historial_tickets (id_ticket, accion, estado_anterior, estado_nuevo)
        VALUES (p_id_ticket, CONCAT('Técnico asignado: ', v_nombre), v_estado, 'En proceso');
    END IF;

    IF v_estado <> 'En proceso' THEN
        INSERT INTO historial_tickets (id_ticket, accion, estado_anterior, estado_nuevo)
        VALUES (p_id_ticket, 'Cambio de estado', v_estado, 'En proceso');
    END IF;

    SELECT CONCAT('Ticket #', p_id_ticket, ' asignado a ', v_nombre) AS mensaje;
END$$

-- ---------------------------------------------------------------------
-- sp_cambiar_estado: ciclo de vida del ticket
--   * un ticket Cerrado no puede reabrirse
--   * para salir de Abierto debe tener técnico asignado
--   * fecha_cierre se completa al Resolver/Cerrar y se limpia si vuelve a estar activo
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_cambiar_estado(IN p_id_ticket INT, IN p_estado VARCHAR(20))
BEGIN
    DECLARE v_estado  VARCHAR(20);
    DECLARE v_tecnico INT;

    IF NOT EXISTS (SELECT 1 FROM tickets WHERE id_ticket = p_id_ticket) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El ticket indicado no existe';
    END IF;

    IF p_estado NOT IN ('Abierto', 'En proceso', 'Resuelto', 'Cerrado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Estado no válido';
    END IF;

    SELECT estado, id_tecnico INTO v_estado, v_tecnico
      FROM tickets WHERE id_ticket = p_id_ticket;

    IF v_estado = 'Cerrado' AND p_estado <> 'Cerrado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un ticket cerrado no puede reabrirse';
    END IF;

    IF p_estado <> 'Abierto' AND v_tecnico IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Debe asignar un técnico antes de cambiar el estado del ticket';
    END IF;

    IF v_estado <> p_estado THEN
        UPDATE tickets
           SET estado = p_estado,
               fecha_cierre = IF(p_estado IN ('Resuelto', 'Cerrado'), COALESCE(fecha_cierre, NOW()), NULL)
         WHERE id_ticket = p_id_ticket;

        INSERT INTO historial_tickets (id_ticket, accion, estado_anterior, estado_nuevo)
        VALUES (p_id_ticket, 'Cambio de estado', v_estado, p_estado);
    END IF;

    SELECT CONCAT('Ticket #', p_id_ticket, ' ahora está ', p_estado) AS mensaje;
END$$

DELIMITER ;
