-- =====================================================================
-- Datos de ejemplo. Se cargan DESPUÉS de los procedimientos, así el historial
-- se genera solo y las asignaciones pasan por las validaciones.
-- =====================================================================

INSERT INTO departamentos (nombre, ubicacion) VALUES
('Administración', 'Piso 1'),
('Docencia', 'Piso 2'),
('Biblioteca', 'Piso 1'),
('Laboratorio de Computación', 'Piso 3');

INSERT INTO usuarios_ti (nombre, email, id_departamento) VALUES
('María González', 'maria.gonzalez@colegio.cl', 1),
('Pedro Fuentes', 'pedro.fuentes@colegio.cl', 2),
('Camila Araya', 'camila.araya@colegio.cl', 2),
('Jorge Pinto', 'jorge.pinto@colegio.cl', 3),
('Sofía Herrera', 'sofia.herrera@colegio.cl', 1),
('Luis Navarro', 'luis.navarro@colegio.cl', 4),
('Isidora Campos', 'isidora.campos@colegio.cl', 4),
('Tomás Bravo', 'tomas.bravo@colegio.cl', 3);

INSERT INTO especialidades (nombre, descripcion) VALUES
('Redes', 'WiFi, cableado, switches e Internet'),
('Hardware', 'Equipos, monitores, teclados y repuestos'),
('Software', 'Instalación y errores de programas'),
('Correo y cuentas', 'Contraseñas, correo institucional y accesos'),
('Impresoras', 'Impresoras, tóner y escáneres'),
('Seguridad', 'Virus, phishing y accesos sospechosos');

INSERT INTO tecnicos (nombre, email, activo) VALUES
('Carlos Muñoz', 'carlos.munoz@soporte.cl', 1),
('Daniela Rojas', 'daniela.rojas@soporte.cl', 1),
('Felipe Soto', 'felipe.soto@soporte.cl', 1),
('Valentina Pérez', 'valentina.perez@soporte.cl', 1),
('Andrés Vera', 'andres.vera@soporte.cl', 0);

INSERT INTO perfiles_tecnico (id_tecnico, telefono, turno, nivel, anios_experiencia) VALUES
(1, '+56 9 1111 1111', 'Mañana', 'Senior', 9),
(2, '+56 9 2222 2222', 'Tarde', 'Semi Senior', 5),
(3, '+56 9 3333 3333', 'Mañana', 'Junior', 2),
(4, '+56 9 4444 4444', 'Tarde', 'Senior', 8),
(5, '+56 9 5555 5555', 'Noche', 'Junior', 1);

-- N:M técnicos <-> especialidades
INSERT INTO tecnico_especialidad (id_tecnico, id_especialidad) VALUES
(1, 1), (1, 6),
(2, 2), (2, 5),
(3, 3), (3, 4),
(4, 1), (4, 2), (4, 3),
(5, 5);

-- Tickets creados con el procedimiento (así quedan en el historial)
CALL sp_crear_ticket('WiFi caído en la sala 3', 'Los notebooks de la sala 3 no logran conectarse a la red WiFi.', 'Alta', 1, 1);
CALL sp_crear_ticket('Computador no enciende', 'El equipo de la biblioteca no da señal de vida al presionar el botón.', 'Media', 4, 2);
CALL sp_crear_ticket('Instalar Office en notebook', 'Se necesita instalar Office en el notebook de docencia.', 'Baja', 3, 3);
CALL sp_crear_ticket('Impresora sin tóner', 'La impresora de administración indica tóner agotado.', 'Media', 5, 5);
CALL sp_crear_ticket('No recuerdo mi contraseña de correo', 'No puedo ingresar al correo institucional desde ayer.', 'Media', 2, 4);
CALL sp_crear_ticket('Correo sospechoso con enlace', 'Llegó un correo que pide datos bancarios, posible phishing.', 'Crítica', 8, 6);
CALL sp_crear_ticket('Monitor parpadea', 'El monitor del laboratorio parpadea y se apaga solo.', 'Media', 6, 2);
CALL sp_crear_ticket('Sistema de notas se cierra solo', 'El programa de notas se cierra al abrir el libro de clases.', 'Alta', 2, 3);
CALL sp_crear_ticket('Sin Internet en el laboratorio', 'Ningún equipo del laboratorio tiene acceso a Internet.', 'Alta', 7, 1);
CALL sp_crear_ticket('Teclado con teclas que fallan', 'Varias teclas del teclado no responden al presionarlas.', 'Baja', 6, 2);

-- Asignaciones (respetan todas las reglas)
CALL sp_asignar_ticket(1, 1);
CALL sp_asignar_ticket(2, 2);
CALL sp_asignar_ticket(3, 3);
CALL sp_asignar_ticket(5, 3);
CALL sp_asignar_ticket(6, 1);
CALL sp_asignar_ticket(8, 4);

-- Ciclo de vida
CALL sp_cambiar_estado(2, 'Resuelto');
CALL sp_cambiar_estado(3, 'Resuelto');
CALL sp_cambiar_estado(3, 'Cerrado');
