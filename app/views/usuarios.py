"""CRUD de usuarios (solicitantes). Muestra datos de departamentos (relación 1:N)."""
import flet as ft

from app import db
from app.ui import (EMAIL_RE, VistaBase, acciones, boton_nuevo, chip, confirmar, encabezado, fila, notificar,
                    opciones, proteger, tabla, validar_campo)


class VistaUsuarios(VistaBase):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.buscador = ft.TextField(label="Buscar por nombre o correo", prefix_icon=ft.Icons.SEARCH, width=320,
                                     on_change=lambda _: self.refrescar())
        self.filtro_depto = ft.Dropdown(label="Departamento", width=260, value="0",
                                        on_change=lambda _: self.refrescar())
        self.controls = [
            encabezado("Usuarios", "Personas que solicitan soporte", boton_nuevo("Nuevo usuario", lambda _: self.formulario())),
            ft.Row([self.buscador, self.filtro_depto], wrap=True),
            self.contador, self.zona,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        deptos = db.departamentos_listar()
        self.filtro_depto.options = [ft.dropdown.Option("0", "Todos")] + opciones(deptos, "id", lambda d: d["nombre"])
        datos = db.usuarios_listar(self.buscador.value or "", int(self.filtro_depto.value or 0) or None)
        filas = [
            fila([
                u["id_usuario"], u["nombre"], u["email"], u["departamento"], u["total_tickets"],
                chip("Activo", "#2e7d32") if u["activo"] else chip("Inactivo", "#757575"),
                acciones(lambda _, u=u: self.formulario(u), lambda _, u=u: self.eliminar(u)),
            ])
            for u in datos
        ]
        self.zona.controls = [tabla(["ID", "Nombre", "Correo", "Departamento", "Tickets", "Estado", "Acciones"], filas)]
        self.contador.value = f"{len(datos)} usuario(s)"

    def formulario(self, usuario: dict | None = None) -> None:
        deptos = db.departamentos_listar()
        nombre = ft.TextField(label="Nombre completo", value=usuario["nombre"] if usuario else "", max_length=100, autofocus=True)
        email = ft.TextField(label="Correo electrónico", value=usuario["email"] if usuario else "", max_length=120)
        depto = ft.Dropdown(label="Departamento", options=opciones(deptos, "id", lambda d: d["nombre"]),
                            value=str(usuario["id_departamento"]) if usuario else None)
        activo = ft.Switch(label="Usuario activo", value=bool(usuario["activo"]) if usuario else True)

        def guardar(_):
            validos = [
                validar_campo(nombre, len(nombre.value.strip()) >= 3, "Mínimo 3 caracteres"),
                validar_campo(email, bool(EMAIL_RE.match(email.value.strip())), "Correo no válido"),
                validar_campo(depto, depto.value is not None, "Selecciona un departamento"),
            ]
            if not all(validos):
                dialogo.update()
                notificar(self.pg, "Revisa los campos marcados", "advertencia")
                return
            ok, _r = proteger(
                self.pg,
                lambda: db.usuario_guardar(nombre.value, email.value, int(depto.value), activo.value,
                                           usuario["id_usuario"] if usuario else None),
                "Usuario guardado correctamente",
            )
            if ok:
                self.pg.close(dialogo)
                self.refrescar()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar usuario" if usuario else "Nuevo usuario"),
            content=ft.Column([nombre, email, depto, activo], tight=True, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: self.pg.close(dialogo)),
                     ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar)],
        )
        self.pg.open(dialogo)

    def eliminar(self, usuario: dict) -> None:
        def borrar():
            ok, _r = proteger(self.pg, lambda: db.usuario_eliminar(usuario["id_usuario"]), "Usuario eliminado")
            if ok:
                self.refrescar()

        confirmar(self.pg, "Eliminar usuario", f"¿Eliminar a «{usuario['nombre']}»?", borrar)
