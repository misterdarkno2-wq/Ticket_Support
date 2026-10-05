-- =====================================================================
-- Consultas de ejemplo (las mismas ideas que usa la aplicación)
-- =====================================================================


-- 1) JOIN: detalle completo de cada ticket (4 tablas relacionadas)
SELECT t.id_ticket, t.titulo, t.prioridad, t.estado,
       u.nombre AS solicitante, d.nombre AS departamento,
       e.nombre AS especialidad,
       COALESCE(tec.nombre, 'Sin asignar') AS tecnico
FROM tickets t
JOIN usuarios_ti u        ON u.id_usuario = t.id_usuario
JOIN departamentos d   ON d.id_departamento = u.id_departamento
JOIN especialidades e  ON e.id_especialidad = t.id_especialidad
LEFT JOIN tecnicos tec ON tec.id_tecnico = t.id_tecnico
ORDER BY t.id_ticket;

-- 2) Agrupación: cantidad de tickets por estado
SELECT estado, COUNT(*) AS total
FROM tickets
GROUP BY estado
ORDER BY total DESC;

-- 3) Agrupación + JOIN: carga de trabajo por técnico
SELECT tec.nombre,
       COUNT(t.id_ticket) AS tickets_totales,
       COALESCE(SUM(t.estado = 'En proceso'), 0) AS en_proceso,
       COALESCE(SUM(t.estado IN ('Resuelto','Cerrado')), 0) AS finalizados
FROM tecnicos tec
LEFT JOIN tickets t ON t.id_tecnico = tec.id_tecnico
GROUP BY tec.id_tecnico, tec.nombre
ORDER BY tickets_totales DESC;

-- 4) Relación N:M: técnicos con sus especialidades
SELECT tec.nombre, GROUP_CONCAT(e.nombre ORDER BY e.nombre SEPARATOR ', ') AS especialidades
FROM tecnicos tec
JOIN tecnico_especialidad te ON te.id_tecnico = tec.id_tecnico
JOIN especialidades e        ON e.id_especialidad = te.id_especialidad
GROUP BY tec.id_tecnico, tec.nombre;

-- 5) Relación 1:1: técnico con su perfil
SELECT tec.nombre, p.turno, p.nivel, p.anios_experiencia
FROM tecnicos tec
JOIN perfiles_tecnico p ON p.id_tecnico = tec.id_tecnico;

-- 6) Historial generado por los procedimientos almacenados
SELECT h.id_ticket, t.titulo, h.accion, h.estado_anterior, h.estado_nuevo, h.fecha
FROM historial_tickets h
JOIN tickets t ON t.id_ticket = h.id_ticket
ORDER BY h.id_historial DESC;
