"""Historial de movimientos de tickets (lo llenan los procedimientos almacenados)."""
import flet as ft

from app import db
from app.ui import VistaBase, chip, COLOR_ESTADO, encabezado, fecha, fila, tabla


def chip_estado(estado):
    return chip(estado, COLOR_ESTADO[estado]) if estado else "—"


class VistaHistorial(VistaBase):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.buscador = ft.TextField(label="Buscar por N° de ticket, título o acción", prefix_icon=ft.Icons.SEARCH,
                                     width=380, on_change=lambda _: self.refrescar())
        self.controls = [
            encabezado("Historial de tickets", "Registrado automáticamente por los procedimientos almacenados de la base de datos"),
            self.buscador, self.contador, self.zona,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        datos = db.historial_listar(self.buscador.value or "")
        filas = [
            fila([f"#{h['id_ticket']}", h["titulo"], h["accion"], chip_estado(h["estado_anterior"]),
                  chip_estado(h["estado_nuevo"]), fecha(h["fecha"])])
            for h in datos
        ]
        self.zona.controls = [tabla(["Ticket", "Título", "Acción", "Estado anterior", "Estado nuevo", "Fecha"], filas)]
        self.contador.value = f"{len(datos)} movimiento(s) (máximo 200)"
