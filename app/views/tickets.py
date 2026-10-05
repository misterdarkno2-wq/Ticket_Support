"""Gestión de tickets: CRUD, búsqueda, filtros y asignación (procedimiento almacenado)."""
import flet as ft

from app import db
from app.ui import (COLOR_ESTADO, COLOR_PRIORIDAD, ESTADOS, PRIORIDADES, VistaBase, acciones, boton_nuevo, chip,
                    confirmar, encabezado, fecha, fila, notificar, opciones, proteger, tabla, validar_campo)


class VistaTickets(VistaBase):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.buscador = ft.TextField(label="Buscar por N°, título o solicitante", prefix_icon=ft.Icons.SEARCH,
                                     width=330, on_change=lambda _: self.refrescar())
        self.filtro_estado = ft.Dropdown(label="Estado", width=170, value="Todos",
                                         options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(e) for e in ESTADOS],
                                         on_change=lambda _: self.refrescar())
        self.filtro_prioridad = ft.Dropdown(label="Prioridad", width=170, value="Todas",
                                            options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(p) for p in PRIORIDADES],
                                            on_change=lambda _: self.refrescar())
        self.controls = [
            encabezado("Tickets", "Solicitudes de soporte técnico", boton_nuevo("Nuevo ticket", lambda _: self.formulario())),
            ft.Row([self.buscador, self.filtro_estado, self.filtro_prioridad], wrap=True),
            self.contador, self.zona,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        estado = "" if self.filtro_estado.value in (None, "Todos") else self.filtro_estado.value
        prioridad = "" if self.filtro_prioridad.value in (None, "Todas") else self.filtro_prioridad.value
        datos = db.tickets_listar(self.buscador.value or "", estado, prioridad)
        filas = []
        for t in datos:
            asignar = ft.IconButton(
                ft.Icons.PERSON_ADD, tooltip="Asignar técnico", icon_color=ft.Colors.TEAL,
                disabled=t["estado"] in ("Resuelto", "Cerrado"), on_click=lambda _, t=t: self.asignar(t))
            filas.append(fila([
                f"#{t['id_ticket']}", t["titulo"], chip(t["prioridad"], COLOR_PRIORIDAD[t["prioridad"]]),
                chip(t["estado"], COLOR_ESTADO[t["estado"]]), t["solicitante"], t["departamento"],
                t["especialidad"], t["tecnico"] or "Sin asignar", fecha(t["fecha_creacion"]), fecha(t["fecha_cierre"]),
                acciones(lambda _, t=t: self.formulario(t), lambda _, t=t: self.eliminar(t), extra=[asignar]),
            ]))
        self.zona.controls = [tabla(
            ["N°", "Título", "Prioridad", "Estado", "Solicitante", "Departamento", "Especialidad", "Técnico",
             "Creado", "Cerrado", "Acciones"], filas)]
        self.contador.value = f"{len(datos)} ticket(s)"

    # ---------------- crear / editar ----------------
    def formulario(self, ticket: dict | None = None) -> None:
        usuarios = db.usuarios_listar()
        especialidades = db.especialidades_listar()
        titulo = ft.TextField(label="Título", value=ticket["titulo"] if ticket else "", max_length=120, autofocus=True)
        descripcion = ft.TextField(label="Descripción del problema", value=ticket["descripcion"] if ticket else "",
                                   multiline=True, min_lines=3, max_lines=5)
        prioridad = ft.Dropdown(label="Prioridad", options=[ft.dropdown.Option(p) for p in PRIORIDADES],
                                value=ticket["prioridad"] if ticket else "Media")
        usuario = ft.Dropdown(label="Solicitante", options=opciones(usuarios, "id_usuario", lambda u: f"{u['nombre']} — {u['departamento']}"),
                              value=str(ticket["id_usuario"]) if ticket else None)
        especialidad = ft.Dropdown(label="Especialidad requerida", options=opciones(especialidades, "id", lambda e: e["nombre"]),
                                   value=str(ticket["id_especialidad"]) if ticket else None)
        estado = ft.Dropdown(label="Estado", options=[ft.dropdown.Option(e) for e in ESTADOS],
                             value=ticket["estado"] if ticket else "Abierto")
        campos = [titulo, descripcion, prioridad, usuario, especialidad] + ([estado] if ticket else [])

        def guardar(_):
            validos = [
                validar_campo(titulo, len(titulo.value.strip()) >= 5, "Mínimo 5 caracteres"),
                validar_campo(descripcion, len(descripcion.value.strip()) >= 10, "Describe el problema (mínimo 10 caracteres)"),
                validar_campo(usuario, usuario.value is not None, "Selecciona un solicitante"),
                validar_campo(especialidad, especialidad.value is not None, "Selecciona una especialidad"),
            ]
            if not all(validos):
                dialogo.update()
                notificar(self.pg, "Revisa los campos marcados", "advertencia")
                return
            if ticket:
                accion = lambda: db.ticket_actualizar(ticket["id_ticket"], titulo.value, descripcion.value,
                                                      prioridad.value, estado.value, int(usuario.value),
                                                      int(especialidad.value))
                mensaje = "Ticket actualizado correctamente"
            else:
                accion = lambda: db.ticket_crear(titulo.value, descripcion.value, prioridad.value,
                                                 int(usuario.value), int(especialidad.value))
                mensaje = "Ticket creado correctamente"
            ok, _r = proteger(self.pg, accion, mensaje)
            if ok:
                self.pg.close(dialogo)
                self.refrescar()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar ticket #{ticket['id_ticket']}" if ticket else "Nuevo ticket"),
            content=ft.Column(campos, tight=True, width=480, scroll=ft.ScrollMode.AUTO, height=460),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: self.pg.close(dialogo)),
                     ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar)],
        )
        self.pg.open(dialogo)

    # ---------------- asignar (procedimiento almacenado) ----------------
    def asignar(self, ticket: dict) -> None:
        ok, candidatos = proteger(self.pg, lambda: db.tecnicos_para_ticket(ticket["id_ticket"]))
        if not ok:
            return
        if not candidatos:
            notificar(self.pg, f"No hay técnicos activos con la especialidad «{ticket['especialidad']}»", "advertencia")
            return
        tecnico = ft.Dropdown(
            label="Técnico", value=str(candidatos[0]["id_tecnico"]),
            options=opciones(candidatos, "id_tecnico", lambda t: f"{t['nombre']} (en proceso: {t['carga']})"))

        def confirmar_asignacion(_):
            ok, _r = proteger(self.pg, lambda: db.ticket_asignar(ticket["id_ticket"], int(tecnico.value)))
            if ok:
                self.pg.close(dialogo)
                self.refrescar()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Asignar ticket #{ticket['id_ticket']}"),
            content=ft.Column([ft.Text(f"Especialidad requerida: {ticket['especialidad']}"), tecnico], tight=True, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: self.pg.close(dialogo)),
                     ft.ElevatedButton("Asignar", icon=ft.Icons.PERSON_ADD, on_click=confirmar_asignacion)],
        )
        self.pg.open(dialogo)

    # ---------------- eliminar ----------------
    def eliminar(self, ticket: dict) -> None:
        def borrar():
            ok, _r = proteger(self.pg, lambda: db.ticket_eliminar(ticket["id_ticket"]), "Ticket eliminado")
            if ok:
                self.refrescar()

        confirmar(self.pg, "Eliminar ticket", f"¿Eliminar el ticket #{ticket['id_ticket']} y su historial?", borrar)
