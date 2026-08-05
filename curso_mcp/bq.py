"""Acceso a BigQuery para el servidor del curso.

Trabaja contra un dataset público de BigQuery, así que el alumno no tiene que cargar
datos: basta con un proyecto GCP donde facturar las consultas.

Si no hay credenciales disponibles (por ejemplo al importar el paquete en un test),
`disponible()` devuelve False y el servidor sigue arrancando: los tools devuelven un
error legible en vez de reventar. Esto permite recorrer el notebook aunque el proyecto
todavía no esté configurado.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Dataset público por defecto. Pocas tablas, temática entendible y consultas baratas.
PROYECTO_DATOS = "bigquery-public-data"
DATASET = os.environ.get("CURSO_MCP_DATASET", "austin_bikeshare")

# Tope de bytes que una consulta puede escanear. El curso expone esto a propósito:
# en un servidor MCP remoto, quien paga la consulta es el dueño del servidor, no quien
# la pide, así que el límite es parte del diseño y no una optimización.
LIMITE_BYTES = int(os.environ.get("CURSO_MCP_LIMITE_BYTES", 1_000_000_000))


@dataclass
class Estimacion:
    """Resultado de un dry run: cuánto escanearía una consulta antes de ejecutarla."""

    bytes_escaneados: int
    dentro_del_limite: bool

    @property
    def megabytes(self) -> float:
        return self.bytes_escaneados / 1_000_000


def _cliente():
    from google.cloud import bigquery

    return bigquery.Client()


def disponible() -> bool:
    """¿Hay credenciales y proyecto para hablar con BigQuery?"""
    try:
        _cliente()
        return True
    except Exception:
        return False


def listar_tablas() -> list[str]:
    cliente = _cliente()
    ref = f"{PROYECTO_DATOS}.{DATASET}"
    return [t.table_id for t in cliente.list_tables(ref)]


def describir_tabla(tabla: str) -> list[dict[str, Any]]:
    cliente = _cliente()
    ref = f"{PROYECTO_DATOS}.{DATASET}.{tabla}"
    esquema = cliente.get_table(ref).schema
    return [
        {"columna": c.name, "tipo": c.field_type, "modo": c.mode, "descripcion": c.description}
        for c in esquema
    ]


def estimar(sql: str) -> Estimacion:
    """Dry run: cuánto escanearía la consulta, sin ejecutarla ni facturarla."""
    from google.cloud import bigquery

    cliente = _cliente()
    trabajo = cliente.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    escaneados = trabajo.total_bytes_processed or 0
    return Estimacion(bytes_escaneados=escaneados, dentro_del_limite=escaneados <= LIMITE_BYTES)


def consultar(sql: str, maximo_filas: int = 50) -> list[dict[str, Any]]:
    cliente = _cliente()
    filas = cliente.query(sql).result(max_results=maximo_filas)
    return [dict(f.items()) for f in filas]
