"""Vista genérica para catálogos simples: Departamentos y Especialidades."""
import flet as ft

from app import db
from app.ui import (VistaBase, acciones, boton_nuevo, confirmar, encabezado, fila, notificar, proteger,
                    tabla, validar_campo)

CONFIG_DEPARTAMENTOS = dict(
    titulo="Departamentos", singular="departamento", subtitulo="Áreas de la organización (1 departamento : N usuarios)",
    campo2="Ubicación", columna_total="Usuarios", listar=db.departamentos_listar,
    guardar=db.departamento_guardar, eliminar=db.departamento_eliminar,
)
CONFIG_ESPECIALIDADES = dict(
    titulo="Especialidades", singular="especialidad", subtitulo="Áreas técnicas (N técnicos : M especialidades)",
    campo2="Descripción", columna_total="Técnicos", listar=db.especialidades_listar,
    guardar=db.especialidad_guardar, eliminar=db.especialidad_eliminar,
)


class VistaCatalogo(VistaBase):
    def __init__(self, page: ft.Page, cfg: dict):
        super().__init__(page)
        self.cfg = cfg
        self.buscador = ft.TextField(label=f"Buscar {cfg['singular']}", prefix_icon=ft.Icons.SEARCH, width=320,
                                     on_change=lambda _: self.refrescar())
        self.controls = [
            encabezado(cfg["titulo"], cfg["subtitulo"], boton_nuevo(f"Nuevo {cfg['singular']}", lambda _: self.formulario())),
            self.buscador, self.contador, self.zona,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        datos = self.cfg["listar"](self.buscador.value or "")
        filas = [
            fila([d["id"], d["nombre"], d["detalle"], d["total"],
                  acciones(lambda _, d=d: self.formulario(d), lambda _, d=d: self.eliminar(d))])
            for d in datos
        ]
        self.zona.controls = [tabla(["ID", "Nombre", self.cfg["campo2"], self.cfg["columna_total"], "Acciones"], filas)]
        self.contador.value = f"{len(datos)} registro(s)"

    def formulario(self, registro: dict | None = None) -> None:
        nombre = ft.TextField(label="Nombre", value=registro["nombre"] if registro else "", max_length=80, autofocus=True)
        detalle = ft.TextField(label=self.cfg["campo2"], value=(registro["detalle"] or "") if registro else "",
                               max_length=200)

        def guardar(_):
            if not validar_campo(nombre, len(nombre.value.strip()) >= 3, "Mínimo 3 caracteres"):
                dialogo.update()
                notificar(self.pg, "Revisa los campos marcados", "advertencia")
                return
            ok, _r = proteger(
                self.pg,
                lambda: self.cfg["guardar"](nombre.value, detalle.value, registro["id"] if registro else None),
                f"{self.cfg['singular'].capitalize()} guardado correctamente",
            )
            if ok:
                self.pg.close(dialogo)
                self.refrescar()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(("Editar " if registro else "Nuevo ") + self.cfg["singular"]),
            content=ft.Column([nombre, detalle], tight=True, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: self.pg.close(dialogo)),
                     ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar)],
        )
        self.pg.open(dialogo)

    def eliminar(self, registro: dict) -> None:
        def borrar():
            ok, _r = proteger(self.pg, lambda: self.cfg["eliminar"](registro["id"]),
                              f"{self.cfg['singular'].capitalize()} eliminado")
            if ok:
                self.refrescar()

        confirmar(self.pg, "Eliminar", f"¿Eliminar «{registro['nombre']}»? Esta acción no se puede deshacer.", borrar)
