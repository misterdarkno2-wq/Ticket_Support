"""Crea las tablas del sistema en la base indicada en DB_NAME (no crea la base).

Uso:  python init_db.py
Ejecuta los scripts de database/ en orden. Soporta los bloques DELIMITER de los
procedimientos almacenados (pymysql no los entiende, por eso se separan aquí).
"""
from pathlib import Path

import pymysql

from app import config

SCRIPTS = ["01_schema.sql", "02_procedimientos.sql", "03_datos_ejemplo.sql"]
TABLAS = ["historial_tickets", "tickets", "tecnico_especialidad", "perfiles_tecnico",
          "tecnicos", "especialidades", "usuarios_ti", "departamentos"]


def separar_sentencias(texto: str) -> list[str]:
    delimitador = ";"
    sentencias, buffer = [], []
    for linea in texto.splitlines():
        limpia = linea.strip()
        if limpia.upper().startswith("DELIMITER"):
            delimitador = limpia.split(None, 1)[1]
            continue
        if not limpia or limpia.startswith("--"):
            continue
        buffer.append(linea)
        if limpia.endswith(delimitador):
            sentencia = "\n".join(buffer).rstrip()
            sentencias.append(sentencia[: -len(delimitador)].rstrip())
            buffer = []
    return sentencias


def main() -> None:
    conexion = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT, user=config.DB_USER,
        password=config.DB_PASSWORD, database=config.DB_NAME,
        charset="utf8mb4", autocommit=True, connect_timeout=8,
    )
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
                (config.DB_NAME,),
            )
            existentes = {f[0].lower() for f in cursor.fetchall()}
            choques = [t for t in TABLAS if t in existentes]
            if choques:
                print(f"ATENCIÓN: en '{config.DB_NAME}' ya existen: {', '.join(choques)}")
                print("Este script las BORRARÁ y las volverá a crear.")
                if input("Escribe BORRAR solo si todas son de ESTE proyecto (Enter cancela): ") != "BORRAR":
                    print("Cancelado, no se tocó nada.")
                    return
            for nombre in SCRIPTS:
                ruta = Path(__file__).parent / "database" / nombre
                n = 0
                for sentencia in separar_sentencias(ruta.read_text(encoding="utf-8")):
                    if sentencia.upper().startswith(("CREATE DATABASE", "USE ")):
                        continue  # se usa la base que ya tienes
                    cursor.execute(sentencia)
                    while cursor.nextset():
                        pass
                    n += 1
                print(f"OK  {nombre}  ({n} sentencias)")
        print(f"\nListo: tablas y procedimientos creados en '{config.DB_NAME}'.")
    except pymysql.MySQLError as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
