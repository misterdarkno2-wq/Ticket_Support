"""Pantalla principal: resumen general (consultas con GROUP BY)."""
import flet as ft

from app import db
from app.ui import COLOR_ESTADO, ESTADOS, VistaBase, encabezado, fila, tabla


def tarjeta(titulo: str, valor, icono, color) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icono, color=color, size=34),
                ft.Column([ft.Text(str(valor), size=26, weight=ft.FontWeight.BOLD),
                           ft.Text(titulo, color=ft.Colors.GREY_700)], spacing=0),
            ],
            spacing=14,
        ),
        padding=18,
        width=230,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.06, color),
        border=ft.border.all(1, ft.Colors.with_opacity(0.25, color)),
    )


class VistaInicio(VistaBase):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.tarjetas = ft.Row(wrap=True, spacing=14, run_spacing=14)
        self.carga = ft.Row([], scroll=ft.ScrollMode.AUTO)
        self.especialidades = ft.Column(spacing=8)
        self.controls = [
            encabezado("Panel de soporte TI", "Resumen del estado de los tickets de la organización"),
            self.tarjetas,
            ft.Text("Carga de trabajo por técnico", size=18, weight=ft.FontWeight.W_600),
            self.carga,
            ft.Text("Tickets por especialidad", size=18, weight=ft.FontWeight.W_600),
            self.especialidades,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        totales = db.totales_generales()
        por_estado = {f["estado"]: f["total"] for f in db.resumen_por_estado()}
        self.tarjetas.controls = [
            tarjeta("Tickets totales", totales["tickets"], ft.Icons.CONFIRMATION_NUMBER, ft.Colors.INDIGO),
            tarjeta("Usuarios", totales["usuarios"], ft.Icons.PEOPLE, ft.Colors.TEAL),
            tarjeta("Técnicos activos", totales["tecnicos"], ft.Icons.ENGINEERING, ft.Colors.PURPLE),
        ] + [tarjeta(e, por_estado.get(e, 0), ft.Icons.CIRCLE, COLOR_ESTADO[e]) for e in ESTADOS]

        filas = [
            fila([f["nombre"], f["total"], int(f["en_proceso"]), int(f["finalizados"])])
            for f in db.resumen_por_tecnico()
        ]
        self.carga.controls = [tabla(["Técnico", "Tickets asignados", "En proceso", "Finalizados"], filas)]

        datos = db.resumen_por_especialidad()
        maximo = max([d["total"] for d in datos] + [1])
        self.especialidades.controls = [
            ft.Row(
                [
                    ft.Text(d["nombre"], width=160),
                    ft.ProgressBar(value=d["total"] / maximo, width=300, color=ft.Colors.INDIGO),
                    ft.Text(str(d["total"])),
                ]
            )
            for d in datos
        ]
