# Diagrama Entidad-Relación

```mermaid
erDiagram
    DEPARTAMENTOS {
        int id_departamento PK
        varchar nombre UK
        varchar ubicacion
    }
    USUARIOS_TI {
        int id_usuario PK
        varchar nombre
        varchar email UK
        int id_departamento FK
        tinyint activo
    }
    TECNICOS {
        int id_tecnico PK
        varchar nombre
        varchar email UK
        tinyint activo
    }
    PERFILES_TECNICO {
        int id_tecnico PK, FK
        varchar telefono
        enum turno
        enum nivel
        tinyint anios_experiencia
    }
    ESPECIALIDADES {
        int id_especialidad PK
        varchar nombre UK
        varchar descripcion
    }
    TECNICO_ESPECIALIDAD {
        int id_tecnico PK, FK
        int id_especialidad PK, FK
    }
    TICKETS {
        int id_ticket PK
        varchar titulo
        text descripcion
        enum prioridad
        enum estado
        int id_usuario FK
        int id_tecnico FK
        int id_especialidad FK
        datetime fecha_creacion
        datetime fecha_cierre
    }
    HISTORIAL_TICKETS {
        int id_historial PK
        int id_ticket FK
        varchar accion
        varchar estado_anterior
        varchar estado_nuevo
        datetime fecha
    }
    DEPARTAMENTOS ||--o{ USUARIOS_TI : "1:N"
    USUARIOS_TI ||--o{ TICKETS : "1:N"
    TECNICOS ||--o| PERFILES_TECNICO : "1:1"
    TECNICOS ||--o{ TECNICO_ESPECIALIDAD : "N:M"
    ESPECIALIDADES ||--o{ TECNICO_ESPECIALIDAD : "N:M"
    TECNICOS |o--o{ TICKETS : "1:N"
    ESPECIALIDADES ||--o{ TICKETS : "1:N"
    TICKETS ||--o{ HISTORIAL_TICKETS : "1:N"
```

## Reglas de negocio
- Un ticket cerrado no puede reabrirse (`sp_cambiar_estado`).
- Un ticket no puede estar En proceso, Resuelto o Cerrado sin técnico (`sp_cambiar_estado` y `CHECK` `chk_ticket_estado_tecnico`).
- `fecha_cierre` existe solo si el ticket está Resuelto o Cerrado (`CHECK` `chk_ticket_fecha_cierre`).
- Solo se asigna un técnico activo, con la especialidad del ticket y menos de 5 tickets en proceso (`sp_asignar_ticket`).
- Solo usuarios activos crean tickets (`sp_crear_ticket`).
- No se puede borrar un usuario, técnico, departamento o especialidad que tenga tickets asociados (`ON DELETE RESTRICT`); se desactiva.
