"""Componentes reutilizables de la interfaz (mensajes, diálogos, tablas, chips)."""
import re

import flet as ft

from app import db

ESTADOS = ["Abierto", "En proceso", "Resuelto", "Cerrado"]
PRIORIDADES = ["Baja", "Media", "Alta", "Crítica"]

COLOR_ESTADO = {
    "Abierto": ft.Colors.BLUE_600,
    "En proceso": ft.Colors.ORANGE_700,
    "Resuelto": ft.Colors.GREEN_600,
    "Cerrado": ft.Colors.GREY_600,
}
COLOR_PRIORIDAD = {
    "Baja": ft.Colors.GREEN_600,
    "Media": ft.Colors.BLUE_600,
    "Alta": ft.Colors.ORANGE_700,
    "Crítica": ft.Colors.RED_700,
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


# --------------------------- mensajes --------------------------------
def notificar(page: ft.Page, mensaje: str, tipo: str = "exito") -> None:
    """Muestra un mensaje claro: tipo = exito | advertencia | error."""
    estilos = {
        "exito": (ft.Colors.GREEN_700, ft.Icons.CHECK_CIRCLE),
        "advertencia": (ft.Colors.ORANGE_800, ft.Icons.WARNING_AMBER),
        "error": (ft.Colors.RED_700, ft.Icons.ERROR),
    }
    color, icono = estilos.get(tipo, estilos["error"])
    page.open(
        ft.SnackBar(
            content=ft.Row(
                [ft.Icon(icono, color=ft.Colors.WHITE), ft.Text(mensaje, color=ft.Colors.WHITE, expand=True)]
            ),
            bgcolor=color,
            duration=4500,
        )
    )


def proteger(page: ft.Page, funcion, exito: str | None = None):
    """Ejecuta una operación de BD sin que la app se cierre si falla.

    Devuelve (True, resultado) si salió bien o (False, None) si hubo un error.
    """
    try:
        resultado = funcion()
    except db.DBError as error:
        notificar(page, error.mensaje, error.tipo)
        return False, None
    except Exception as error:  # cualquier fallo inesperado: se informa, no se cierra la app
        notificar(page, f"Ocurrió un error inesperado: {error}", "error")
        return False, None
    mensaje = exito or (resultado if isinstance(resultado, str) else None)
    if mensaje:
        notificar(page, mensaje, "exito")
    return True, resultado


# --------------------------- diálogos --------------------------------
def confirmar(page: ft.Page, titulo: str, mensaje: str, al_confirmar) -> None:
    def aceptar(_):
        page.close(dialogo)
        al_confirmar()

    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo),
        content=ft.Text(mensaje),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo)),
            ft.ElevatedButton("Eliminar", icon=ft.Icons.DELETE, bgcolor=ft.Colors.RED_600,
                              color=ft.Colors.WHITE, on_click=aceptar),
        ],
    )
    page.open(dialogo)


def validar_campo(campo, condicion: bool, mensaje: str) -> bool:
    campo.error_text = None if condicion else mensaje
    return condicion


# --------------------------- tablas y piezas -------------------------
def chip(texto: str, color) -> ft.Container:
    return ft.Container(
        content=ft.Text(texto, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
        border_radius=12,
    )


def tabla(columnas: list[str], filas: list[ft.DataRow]) -> ft.DataTable:
    return ft.DataTable(
        columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columnas],
        rows=filas,
        heading_row_color=ft.Colors.with_opacity(0.08, ft.Colors.INDIGO),
        column_spacing=22,
        data_row_min_height=46,
    )


def fila(celdas: list) -> ft.DataRow:
    controles = []
    for celda in celdas:
        if isinstance(celda, ft.Control):
            controles.append(ft.DataCell(celda))
        else:
            controles.append(ft.DataCell(ft.Text("—" if celda in (None, "") else str(celda))))
    return ft.DataRow(cells=controles)


def encabezado(titulo: str, subtitulo: str, boton: ft.Control | None = None) -> ft.Row:
    textos = ft.Column(
        [ft.Text(titulo, size=26, weight=ft.FontWeight.BOLD), ft.Text(subtitulo, color=ft.Colors.GREY_700)],
        spacing=2,
        expand=True,
    )
    return ft.Row([textos, boton] if boton else [textos])


def boton_nuevo(texto: str, al_click) -> ft.ElevatedButton:
    return ft.ElevatedButton(texto, icon=ft.Icons.ADD, on_click=al_click, bgcolor=ft.Colors.INDIGO,
                             color=ft.Colors.WHITE)


def acciones(al_editar=None, al_eliminar=None, extra: list | None = None) -> ft.Row:
    botones = list(extra or [])
    if al_editar:
        botones.append(ft.IconButton(ft.Icons.EDIT, tooltip="Editar", icon_color=ft.Colors.INDIGO, on_click=al_editar))
    if al_eliminar:
        botones.append(ft.IconButton(ft.Icons.DELETE, tooltip="Eliminar", icon_color=ft.Colors.RED_600,
                                     on_click=al_eliminar))
    return ft.Row(botones, spacing=0)


def opciones(filas: list[dict], clave: str, texto) -> list[ft.dropdown.Option]:
    return [ft.dropdown.Option(key=str(f[clave]), text=texto(f)) for f in filas]


def fecha(valor) -> str:
    return valor.strftime("%d-%m-%Y %H:%M") if valor else "—"


# --------------------------- vista base ------------------------------
class VistaBase(ft.Column):
    """Clase base: guarda la página, carga datos de forma segura y refresca."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14)
        self.pg = page
        self.zona = ft.Row([], scroll=ft.ScrollMode.AUTO)
        self.contador = ft.Text("", color=ft.Colors.GREY_700, size=12)

    def cargar(self) -> None:  # lo implementa cada vista
        raise NotImplementedError

    def cargar_seguro(self) -> None:
        try:
            self.cargar()
        except db.DBError as error:
            self.zona.controls = [ft.Text(error.mensaje, color=ft.Colors.RED_700)]
            notificar(self.pg, error.mensaje, error.tipo)
        except Exception as error:
            self.zona.controls = [ft.Text(f"Error inesperado: {error}", color=ft.Colors.RED_700)]
            notificar(self.pg, f"Error inesperado: {error}", "error")

    def refrescar(self) -> None:
        self.cargar_seguro()
        self.update()
