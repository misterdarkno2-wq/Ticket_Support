"""Sistema de Tickets de Soporte TI - punto de entrada de la aplicación Flet."""
import flet as ft

from app.ui import notificar
from app.views.catalogo import CONFIG_DEPARTAMENTOS, CONFIG_ESPECIALIDADES, VistaCatalogo
from app.views.historial import VistaHistorial
from app.views.inicio import VistaInicio
from app.views.tecnicos import VistaTecnicos
from app.views.tickets import VistaTickets
from app.views.usuarios import VistaUsuarios

# (etiqueta, icono, icono seleccionado, constructor de la vista)
SECCIONES = [
    ("Inicio", ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, VistaInicio),
    ("Tickets", ft.Icons.CONFIRMATION_NUMBER_OUTLINED, ft.Icons.CONFIRMATION_NUMBER, VistaTickets),
    ("Usuarios", ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, VistaUsuarios),
    ("Técnicos", ft.Icons.ENGINEERING_OUTLINED, ft.Icons.ENGINEERING, VistaTecnicos),
    ("Departamentos", ft.Icons.BUSINESS_OUTLINED, ft.Icons.BUSINESS, lambda p: VistaCatalogo(p, CONFIG_DEPARTAMENTOS)),
    ("Especialidades", ft.Icons.SCHOOL_OUTLINED, ft.Icons.SCHOOL, lambda p: VistaCatalogo(p, CONFIG_ESPECIALIDADES)),
    ("Historial", ft.Icons.HISTORY, ft.Icons.HISTORY, VistaHistorial),
]


def main(page: ft.Page) -> None:
    page.title = "Sistema de Tickets de Soporte TI"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 1320
    page.window.height = 820
    page.window.min_width = 900

    contenido = ft.Container(expand=True, padding=24)

    def mostrar(indice: int) -> None:
        try:
            contenido.content = SECCIONES[indice][3](page)
        except Exception as error:  # la app sigue viva aunque una vista falle
            contenido.content = ft.Text(f"No se pudo abrir la sección: {error}", color=ft.Colors.RED_700)
            notificar(page, f"No se pudo abrir la sección: {error}", "error")
        page.update()

    menu = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=96,
        leading=ft.Container(
            content=ft.Column([ft.Icon(ft.Icons.SUPPORT_AGENT, size=34, color=ft.Colors.INDIGO),
                               ft.Text("Soporte TI", size=12, weight=ft.FontWeight.BOLD)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.padding.only(top=12, bottom=8),
        ),
        destinations=[ft.NavigationRailDestination(icon=i, selected_icon=s, label=n) for n, i, s, _ in SECCIONES],
        on_change=lambda e: mostrar(e.control.selected_index),
    )

    page.add(ft.Row([menu, ft.VerticalDivider(width=1), contenido], expand=True))
    mostrar(0)


if __name__ == "__main__":
    ft.app(target=main)
