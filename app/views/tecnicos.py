"""CRUD de técnicos: perfil (1:1) y especialidades (N:M) en un solo formulario."""
import flet as ft

from app import db
from app.ui import (EMAIL_RE, VistaBase, acciones, boton_nuevo, chip, confirmar, encabezado, fila, notificar,
                    proteger, tabla, validar_campo)

TURNOS = ["Mañana", "Tarde", "Noche"]
NIVELES = ["Junior", "Semi Senior", "Senior"]


class VistaTecnicos(VistaBase):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.buscador = ft.TextField(label="Buscar por nombre o correo", prefix_icon=ft.Icons.SEARCH, width=320,
                                     on_change=lambda _: self.refrescar())
        self.controls = [
            encabezado("Técnicos", "Equipo de soporte, su perfil y sus especialidades",
                       boton_nuevo("Nuevo técnico", lambda _: self.formulario())),
            self.buscador, self.contador, self.zona,
        ]
        self.cargar_seguro()

    def cargar(self) -> None:
        datos = db.tecnicos_listar(self.buscador.value or "")
        filas = [
            fila([
                t["id_tecnico"], t["nombre"], t["email"], t["turno"], t["nivel"], t["anios_experiencia"],
                t["especialidades"], t["tickets_activos"],
                chip("Activo", "#2e7d32") if t["activo"] else chip("Inactivo", "#757575"),
                acciones(lambda _, t=t: self.formulario(t), lambda _, t=t: self.eliminar(t)),
            ])
            for t in datos
        ]
        self.zona.controls = [tabla(
            ["ID", "Nombre", "Correo", "Turno", "Nivel", "Años exp.", "Especialidades", "En proceso", "Estado", "Acciones"],
            filas)]
        self.contador.value = f"{len(datos)} técnico(s)"

    def formulario(self, tecnico: dict | None = None) -> None:
        especialidades = db.especialidades_listar()
        marcadas = db.tecnico_especialidades_ids(tecnico["id_tecnico"]) if tecnico else set()
        nombre = ft.TextField(label="Nombre completo", value=tecnico["nombre"] if tecnico else "", max_length=100, autofocus=True)
        email = ft.TextField(label="Correo electrónico", value=tecnico["email"] if tecnico else "", max_length=120)
        telefono = ft.TextField(label="Teléfono (opcional)", value=(tecnico["telefono"] or "") if tecnico else "", max_length=20)
        turno = ft.Dropdown(label="Turno", options=[ft.dropdown.Option(t) for t in TURNOS],
                            value=(tecnico["turno"] if tecnico and tecnico["turno"] else "Mañana"), expand=True)
        nivel = ft.Dropdown(label="Nivel", options=[ft.dropdown.Option(n) for n in NIVELES],
                            value=(tecnico["nivel"] if tecnico and tecnico["nivel"] else "Junior"), expand=True)
        anios = ft.TextField(label="Años de experiencia", keyboard_type=ft.KeyboardType.NUMBER,
                             value=str(tecnico["anios_experiencia"] or 0) if tecnico else "0")
        activo = ft.Switch(label="Técnico activo", value=bool(tecnico["activo"]) if tecnico else True)
        checks = [ft.Checkbox(label=e["nombre"], value=e["id"] in marcadas, data=e["id"]) for e in especialidades]

        def guardar(_):
            anios_ok = anios.value.strip().isdigit() and 0 <= int(anios.value) <= 50
            validos = [
                validar_campo(nombre, len(nombre.value.strip()) >= 3, "Mínimo 3 caracteres"),
                validar_campo(email, bool(EMAIL_RE.match(email.value.strip())), "Correo no válido"),
                validar_campo(anios, anios_ok, "Ingresa un número entre 0 y 50"),
            ]
            elegidas = [c.data for c in checks if c.value]
            if not all(validos):
                dialogo.update()
                notificar(self.pg, "Revisa los campos marcados", "advertencia")
                return
            if not elegidas:
                notificar(self.pg, "Selecciona al menos una especialidad para el técnico", "advertencia")
                return
            datos = dict(nombre=nombre.value, email=email.value, telefono=telefono.value, turno=turno.value,
                         nivel=nivel.value, anios=int(anios.value), activo=activo.value)
            ok, _r = proteger(
                self.pg,
                lambda: db.tecnico_guardar(datos, elegidas, tecnico["id_tecnico"] if tecnico else None),
                "Técnico guardado correctamente",
            )
            if ok:
                self.pg.close(dialogo)
                self.refrescar()

        contenido = ft.Column(
            [nombre, email, telefono, ft.Row([turno, nivel]), anios, activo,
             ft.Text("Especialidades (relación N:M)", weight=ft.FontWeight.W_600), *checks],
            tight=True, width=440, scroll=ft.ScrollMode.AUTO, height=520,
        )
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar técnico" if tecnico else "Nuevo técnico"),
            content=contenido,
            actions=[ft.TextButton("Cancelar", on_click=lambda _: self.pg.close(dialogo)),
                     ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar)],
        )
        self.pg.open(dialogo)

    def eliminar(self, tecnico: dict) -> None:
        def borrar():
            ok, _r = proteger(self.pg, lambda: db.tecnico_eliminar(tecnico["id_tecnico"]), "Técnico eliminado")
            if ok:
                self.refrescar()

        confirmar(self.pg, "Eliminar técnico",
                  f"¿Eliminar a «{tecnico['nombre']}»? Se borrará también su perfil y sus especialidades.", borrar)
