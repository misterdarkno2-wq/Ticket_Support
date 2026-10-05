# Guía para la defensa (apunte personal)

**Decisiones clave que debes saber explicar**
- *¿Por qué `perfiles_tecnico` es 1:1?* Su PK es también FK hacia `tecnicos`: no puede haber dos perfiles para un técnico.
- *¿Por qué `tecnico_especialidad`?* Un técnico tiene varias especialidades y una especialidad la tienen varios técnicos (N:M); se resuelve con tabla intermedia y PK compuesta.
- *¿Por qué `ON DELETE RESTRICT` en tickets?* Para no perder historial; si un técnico ya no trabaja, se pone `activo = 0`.
- *¿Por qué no hay triggers?* El servidor no entrega `SUPER` y con *binary logging* activo MySQL rechaza crear triggers (error 1419). Lo reemplacé con procedimientos almacenados que validan y escriben el historial, más `CHECK` en la tabla para que la base rechace estados incoherentes aunque alguien haga un `UPDATE` directo. (Consulta con el profesor que esto sea aceptable.)
- *¿Para qué sirven los procedimientos?* Concentran en un solo lugar las reglas del negocio y dejan cada operación atómica.
- *¿Por qué `usuarios_ti`?* En la base compartida ya existía una tabla `usuarios` de otro proyecto.
- *¿Por qué cada función de `db.py` abre su conexión?* Evita conexiones caídas por inactividad; `transaccion()` hace commit o rollback.

**Demostración sugerida (5 min)**
1. DER (`docs/DER.md`) y las tablas en DBeaver: señalar 1:1, 1:N y N:M.
2. App: Tickets → buscar "wifi" y filtrar por estado.
3. Crear un ticket → ir a Historial (lo registra `sp_crear_ticket`).
4. Asignar el ticket (`sp_asignar_ticket`) → intentar asignar a un técnico sin la especialidad (advertencia).
5. Editar un ticket sin técnico a "En proceso" → `sp_cambiar_estado` lo bloquea.
6. Inicio: resumen con `GROUP BY`; mostrar la consulta de `database/04_consultas.sql`.
7. `git log --oneline`.
