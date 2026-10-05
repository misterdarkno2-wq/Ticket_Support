"""Capa de acceso a datos: toda la comunicación con MySQL/MariaDB usa PyMySQL.

La interfaz (Flet) nunca escribe SQL: solo llama a las funciones de este módulo.
Cada operación abre una conexión, ejecuta dentro de una transacción
(commit si todo sale bien, rollback si algo falla) y la cierra.
"""
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from app import config


class DBError(Exception):
    """Error de base de datos con mensaje legible para el usuario final.

    tipo: "advertencia" (regla de negocio / integridad) o "error" (falla técnica).
    """

    def __init__(self, mensaje: str, tipo: str = "error"):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.tipo = tipo


def _traducir(error: pymysql.MySQLError) -> DBError:
    """Convierte errores de MySQL en mensajes claros."""
    codigo = error.args[0] if error.args else 0
    detalle = error.args[1] if len(error.args) > 1 else str(error)

    if codigo == 1062:
        return DBError("Ya existe un registro con ese valor (dato duplicado).", "advertencia")
    if codigo == 1451:
        return DBError(
            "No se puede eliminar: el registro está siendo usado por otros datos "
            "(por ejemplo tickets). Considera desactivarlo en vez de borrarlo.",
            "advertencia",
        )
    if codigo == 1452:
        return DBError("La referencia seleccionada no existe en la base de datos.", "advertencia")
    if codigo in (4025, 3819):
        return DBError("Los datos no cumplen las reglas de validación de la base de datos.", "advertencia")
    if codigo == 1644:  # SIGNAL SQLSTATE '45000' lanzado por triggers y procedimientos
        return DBError(str(detalle), "advertencia")
    if codigo in (1045, 1698):
        return DBError("Usuario o contraseña de MySQL incorrectos. Revisa tu archivo .env.")
    if codigo == 1049:
        return DBError("La base de datos no existe. Ejecuta primero: python init_db.py")
    if codigo in (2002, 2003, 2006, 2013):
        return DBError("No se pudo conectar con el servidor MySQL. ¿Está encendido? Revisa el .env.")
    return DBError(f"Error de base de datos ({codigo}): {detalle}")


@contextmanager
def transaccion():
    """Entrega un cursor dentro de una transacción."""
    conexion = None
    try:
        conexion = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
        )
        with conexion.cursor() as cursor:
            yield cursor
        conexion.commit()
    except pymysql.MySQLError as error:
        if conexion:
            conexion.rollback()
        raise _traducir(error) from error
    finally:
        if conexion:
            conexion.close()


def consultar(sql: str, params: tuple | list = ()) -> list[dict]:
    with transaccion() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def ejecutar(sql: str, params: tuple | list = ()) -> int:
    """Ejecuta INSERT/UPDATE/DELETE. Devuelve el id insertado (si aplica)."""
    with transaccion() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid


def _like(texto: str) -> str:
    return f"%{texto.strip()}%"


# ---------------------------------------------------------------------
# DEPARTAMENTOS  (1:N con usuarios)
# ---------------------------------------------------------------------
def departamentos_listar(texto: str = "") -> list[dict]:
    return consultar(
        """
        SELECT d.id_departamento AS id, d.nombre, d.ubicacion AS detalle,
               COUNT(u.id_usuario) AS total
        FROM departamentos d
        LEFT JOIN usuarios_ti u ON u.id_departamento = d.id_departamento
        WHERE d.nombre LIKE %s
        GROUP BY d.id_departamento, d.nombre, d.ubicacion
        ORDER BY d.nombre
        """,
        (_like(texto),),
    )


def departamento_guardar(nombre: str, ubicacion: str, id_: int | None = None) -> None:
    ubicacion = ubicacion.strip() or None
    if id_ is None:
        ejecutar("INSERT INTO departamentos (nombre, ubicacion) VALUES (%s, %s)", (nombre.strip(), ubicacion))
    else:
        ejecutar(
            "UPDATE departamentos SET nombre = %s, ubicacion = %s WHERE id_departamento = %s",
            (nombre.strip(), ubicacion, id_),
        )


def departamento_eliminar(id_: int) -> None:
    ejecutar("DELETE FROM departamentos WHERE id_departamento = %s", (id_,))


# ---------------------------------------------------------------------
# ESPECIALIDADES  (N:M con técnicos)
# ---------------------------------------------------------------------
def especialidades_listar(texto: str = "") -> list[dict]:
    return consultar(
        """
        SELECT e.id_especialidad AS id, e.nombre, e.descripcion AS detalle,
               COUNT(te.id_tecnico) AS total
        FROM especialidades e
        LEFT JOIN tecnico_especialidad te ON te.id_especialidad = e.id_especialidad
        WHERE e.nombre LIKE %s
        GROUP BY e.id_especialidad, e.nombre, e.descripcion
        ORDER BY e.nombre
        """,
        (_like(texto),),
    )


def especialidad_guardar(nombre: str, descripcion: str, id_: int | None = None) -> None:
    descripcion = descripcion.strip() or None
    if id_ is None:
        ejecutar("INSERT INTO especialidades (nombre, descripcion) VALUES (%s, %s)", (nombre.strip(), descripcion))
    else:
        ejecutar(
            "UPDATE especialidades SET nombre = %s, descripcion = %s WHERE id_especialidad = %s",
            (nombre.strip(), descripcion, id_),
        )


def especialidad_eliminar(id_: int) -> None:
    ejecutar("DELETE FROM especialidades WHERE id_especialidad = %s", (id_,))


# ---------------------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------------------
def usuarios_listar(texto: str = "", id_departamento: int | None = None) -> list[dict]:
    sql = """
        SELECT u.id_usuario, u.nombre, u.email, u.activo, u.id_departamento,
               d.nombre AS departamento,
               COUNT(t.id_ticket) AS total_tickets
        FROM usuarios_ti u
        JOIN departamentos d ON d.id_departamento = u.id_departamento
        LEFT JOIN tickets t ON t.id_usuario = u.id_usuario
        WHERE (u.nombre LIKE %s OR u.email LIKE %s)
    """
    params: list = [_like(texto), _like(texto)]
    if id_departamento:
        sql += " AND u.id_departamento = %s"
        params.append(id_departamento)
    sql += " GROUP BY u.id_usuario, u.nombre, u.email, u.activo, u.id_departamento, d.nombre ORDER BY u.nombre"
    return consultar(sql, params)


def usuario_guardar(nombre: str, email: str, id_departamento: int, activo: bool, id_: int | None = None) -> None:
    if id_ is None:
        ejecutar(
            "INSERT INTO usuarios_ti (nombre, email, id_departamento, activo) VALUES (%s, %s, %s, %s)",
            (nombre.strip(), email.strip().lower(), id_departamento, int(activo)),
        )
    else:
        ejecutar(
            "UPDATE usuarios_ti SET nombre = %s, email = %s, id_departamento = %s, activo = %s WHERE id_usuario = %s",
            (nombre.strip(), email.strip().lower(), id_departamento, int(activo), id_),
        )


def usuario_eliminar(id_: int) -> None:
    ejecutar("DELETE FROM usuarios_ti WHERE id_usuario = %s", (id_,))


# ---------------------------------------------------------------------
# TÉCNICOS  (1:1 con perfiles_tecnico, N:M con especialidades)
# ---------------------------------------------------------------------
def tecnicos_listar(texto: str = "") -> list[dict]:
    return consultar(
        """
        SELECT t.id_tecnico, t.nombre, t.email, t.activo,
               p.telefono, p.turno, p.nivel, p.anios_experiencia,
               (SELECT GROUP_CONCAT(e.nombre ORDER BY e.nombre SEPARATOR ', ')
                  FROM tecnico_especialidad te
                  JOIN especialidades e ON e.id_especialidad = te.id_especialidad
                 WHERE te.id_tecnico = t.id_tecnico) AS especialidades,
               (SELECT COUNT(*) FROM tickets k
                 WHERE k.id_tecnico = t.id_tecnico AND k.estado = 'En proceso') AS tickets_activos
        FROM tecnicos t
        LEFT JOIN perfiles_tecnico p ON p.id_tecnico = t.id_tecnico
        WHERE (t.nombre LIKE %s OR t.email LIKE %s)
        ORDER BY t.nombre
        """,
        (_like(texto), _like(texto)),
    )


def tecnico_especialidades_ids(id_tecnico: int) -> set[int]:
    filas = consultar("SELECT id_especialidad FROM tecnico_especialidad WHERE id_tecnico = %s", (id_tecnico,))
    return {f["id_especialidad"] for f in filas}


def tecnico_guardar(datos: dict, especialidades: list[int], id_: int | None = None) -> None:
    """Guarda técnico + perfil (1:1) + especialidades (N:M) en UNA sola transacción."""
    with transaccion() as cursor:
        if id_ is None:
            cursor.execute(
                "INSERT INTO tecnicos (nombre, email, activo) VALUES (%s, %s, %s)",
                (datos["nombre"].strip(), datos["email"].strip().lower(), int(datos["activo"])),
            )
            id_ = cursor.lastrowid
            cursor.execute(
                "INSERT INTO perfiles_tecnico (id_tecnico, telefono, turno, nivel, anios_experiencia) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_, datos["telefono"].strip() or None, datos["turno"], datos["nivel"], datos["anios"]),
            )
        else:
            cursor.execute(
                "UPDATE tecnicos SET nombre = %s, email = %s, activo = %s WHERE id_tecnico = %s",
                (datos["nombre"].strip(), datos["email"].strip().lower(), int(datos["activo"]), id_),
            )
            cursor.execute(
                "INSERT INTO perfiles_tecnico (id_tecnico, telefono, turno, nivel, anios_experiencia) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE telefono = VALUES(telefono), turno = VALUES(turno), "
                "nivel = VALUES(nivel), anios_experiencia = VALUES(anios_experiencia)",
                (id_, datos["telefono"].strip() or None, datos["turno"], datos["nivel"], datos["anios"]),
            )
            cursor.execute("DELETE FROM tecnico_especialidad WHERE id_tecnico = %s", (id_,))
        for id_esp in especialidades:
            cursor.execute(
                "INSERT INTO tecnico_especialidad (id_tecnico, id_especialidad) VALUES (%s, %s)", (id_, id_esp)
            )


def tecnico_eliminar(id_: int) -> None:
    ejecutar("DELETE FROM tecnicos WHERE id_tecnico = %s", (id_,))


def tecnicos_para_ticket(id_ticket: int) -> list[dict]:
    """Técnicos activos con la especialidad que pide el ticket, con su carga actual."""
    return consultar(
        """
        SELECT tec.id_tecnico, tec.nombre,
               (SELECT COUNT(*) FROM tickets k
                 WHERE k.id_tecnico = tec.id_tecnico AND k.estado = 'En proceso') AS carga
        FROM tickets t
        JOIN tecnico_especialidad te ON te.id_especialidad = t.id_especialidad
        JOIN tecnicos tec ON tec.id_tecnico = te.id_tecnico
        WHERE t.id_ticket = %s AND tec.activo = 1
        ORDER BY carga, tec.nombre
        """,
        (id_ticket,),
    )


# ---------------------------------------------------------------------
# TICKETS (JOIN de 5 tablas)
# ---------------------------------------------------------------------
def tickets_listar(texto: str = "", estado: str = "", prioridad: str = "") -> list[dict]:
    sql = """
        SELECT t.id_ticket, t.titulo, t.descripcion, t.prioridad, t.estado,
               t.id_usuario, t.id_tecnico, t.id_especialidad,
               t.fecha_creacion, t.fecha_cierre,
               u.nombre AS solicitante, d.nombre AS departamento,
               e.nombre AS especialidad,
               tec.nombre AS tecnico
        FROM tickets t
        JOIN usuarios_ti u         ON u.id_usuario = t.id_usuario
        JOIN departamentos d    ON d.id_departamento = u.id_departamento
        JOIN especialidades e   ON e.id_especialidad = t.id_especialidad
        LEFT JOIN tecnicos tec  ON tec.id_tecnico = t.id_tecnico
        WHERE (t.titulo LIKE %s OR u.nombre LIKE %s OR CAST(t.id_ticket AS CHAR) = %s)
    """
    params: list = [_like(texto), _like(texto), texto.strip().lstrip("#")]
    if estado:
        sql += " AND t.estado = %s"
        params.append(estado)
    if prioridad:
        sql += " AND t.prioridad = %s"
        params.append(prioridad)
    sql += " ORDER BY t.id_ticket DESC"
    return consultar(sql, params)


def ticket_crear(titulo: str, descripcion: str, prioridad: str, id_usuario: int, id_especialidad: int) -> int:
    """Crea el ticket con el procedimiento sp_crear_ticket (que también registra el historial)."""
    with transaccion() as cursor:
        cursor.execute(
            "CALL sp_crear_ticket(%s, %s, %s, %s, %s)",
            (titulo.strip(), descripcion.strip(), prioridad, id_usuario, id_especialidad),
        )
        return cursor.fetchone()["id_ticket"]


def ticket_actualizar(
    id_: int, titulo: str, descripcion: str, prioridad: str, estado: str, id_usuario: int, id_especialidad: int
) -> None:
    """Actualiza los datos del ticket; si cambió el estado usa sp_cambiar_estado (todo en una transacción)."""
    with transaccion() as cursor:
        cursor.execute("SELECT estado FROM tickets WHERE id_ticket = %s FOR UPDATE", (id_,))
        actual = cursor.fetchone()
        if actual is None:
            raise DBError("El ticket ya no existe.", "advertencia")
        cursor.execute(
            "UPDATE tickets SET titulo = %s, descripcion = %s, prioridad = %s, "
            "id_usuario = %s, id_especialidad = %s WHERE id_ticket = %s",
            (titulo.strip(), descripcion.strip(), prioridad, id_usuario, id_especialidad, id_),
        )
        if actual["estado"] != estado:
            cursor.execute("CALL sp_cambiar_estado(%s, %s)", (id_, estado))


def ticket_eliminar(id_: int) -> None:
    ejecutar("DELETE FROM tickets WHERE id_ticket = %s", (id_,))


def ticket_asignar(id_ticket: int, id_tecnico: int) -> str:
    """Llama al procedimiento almacenado sp_asignar_ticket. Devuelve su mensaje."""
    with transaccion() as cursor:
        cursor.execute("CALL sp_asignar_ticket(%s, %s)", (id_ticket, id_tecnico))
        fila = cursor.fetchone()
    return fila["mensaje"] if fila else "Ticket asignado"


# ---------------------------------------------------------------------
# HISTORIAL (llenado por los procedimientos) Y RESÚMENES (GROUP BY)
# ---------------------------------------------------------------------
def historial_listar(texto: str = "") -> list[dict]:
    return consultar(
        """
        SELECT h.id_historial, h.id_ticket, t.titulo, h.accion,
               h.estado_anterior, h.estado_nuevo, h.fecha
        FROM historial_tickets h
        JOIN tickets t ON t.id_ticket = h.id_ticket
        WHERE (t.titulo LIKE %s OR h.accion LIKE %s OR CAST(h.id_ticket AS CHAR) = %s)
        ORDER BY h.id_historial DESC
        LIMIT 200
        """,
        (_like(texto), _like(texto), texto.strip().lstrip("#")),
    )


def resumen_por_estado() -> list[dict]:
    return consultar("SELECT estado, COUNT(*) AS total FROM tickets GROUP BY estado")


def resumen_por_tecnico() -> list[dict]:
    return consultar(
        """
        SELECT tec.nombre,
               COUNT(t.id_ticket) AS total,
               COALESCE(SUM(t.estado = 'En proceso'), 0) AS en_proceso,
               COALESCE(SUM(t.estado IN ('Resuelto', 'Cerrado')), 0) AS finalizados
        FROM tecnicos tec
        LEFT JOIN tickets t ON t.id_tecnico = tec.id_tecnico
        GROUP BY tec.id_tecnico, tec.nombre
        ORDER BY total DESC, tec.nombre
        """
    )


def resumen_por_especialidad() -> list[dict]:
    return consultar(
        """
        SELECT e.nombre, COUNT(t.id_ticket) AS total
        FROM especialidades e
        LEFT JOIN tickets t ON t.id_especialidad = e.id_especialidad
        GROUP BY e.id_especialidad, e.nombre
        ORDER BY total DESC, e.nombre
        """
    )


def totales_generales() -> dict:
    fila = consultar(
        """
        SELECT (SELECT COUNT(*) FROM tickets)  AS tickets,
               (SELECT COUNT(*) FROM usuarios_ti) AS usuarios,
               (SELECT COUNT(*) FROM tecnicos WHERE activo = 1) AS tecnicos
        """
    )
    return fila[0]
