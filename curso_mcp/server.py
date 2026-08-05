"""El servidor MCP del curso.

Un único servidor que crece a lo largo de las cuatro sesiones. Se despliega entero en la
sesión 1 y cada sesión consume la parte que le toca, de modo que no hace falta volver a
desplegar en cada módulo.

    from curso_mcp.server import crear_servidor
    mcp = crear_servidor()
    app = mcp.streamable_http_app()
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from pydantic import BaseModel, Field

from curso_mcp import bq

INSTRUCCIONES = """
Servidor de ejemplo del curso de MCP. Expone un dataset público de BigQuery:
permite listar tablas, consultar su esquema y ejecutar consultas SQL acotadas.
Empieza siempre por `listar_tablas` para saber qué hay disponible.
""".strip()


class ConfirmacionDeGasto(BaseModel):
    """Esquema del formulario que el host presenta al usuario antes de una consulta cara."""

    continuar: bool = Field(description="¿Ejecutar la consulta aunque escanee más de lo previsto?")


def crear_servidor(*, con_apps: bool = True) -> MCPServer:
    """Construye el servidor del curso.

    Args:
        con_apps: si se registra la extensión MCP Apps (sesión 4). Se puede apagar para
            ver en el notebook cómo cambia la respuesta de `server/discover` cuando el
            servidor deja de anunciar una extensión.
    """
    extensiones: list[Any] = []
    if con_apps:
        from curso_mcp.widget import construir_extension_apps

        extensiones.append(construir_extension_apps())

    mcp = MCPServer(
        name="curso-mcp-bigquery",
        title="Curso MCP · BigQuery",
        version="0.1.0",
        instructions=INSTRUCCIONES,
        extensions=extensiones,
    )

    # ---------------------------------------------------------------- Tools (sesión 1)

    @mcp.tool(
        title="Listar tablas",
        description="Devuelve los nombres de las tablas disponibles en el dataset del curso.",
    )
    def listar_tablas() -> list[str]:
        if not bq.disponible():
            raise RuntimeError("Sin credenciales de BigQuery. Revisa el módulo 0 del notebook 1.")
        return bq.listar_tablas()

    @mcp.tool(
        title="Describir tabla",
        description=(
            "Devuelve el esquema de una tabla: columnas, tipos y descripción. "
            "Úsalo antes de escribir una consulta para no inventar nombres de columna."
        ),
    )
    def describir_tabla(tabla: str) -> list[dict[str, Any]]:
        if not bq.disponible():
            raise RuntimeError("Sin credenciales de BigQuery. Revisa el módulo 0 del notebook 1.")
        return bq.describir_tabla(tabla)

    # ------------------------------------------- Tool con interacción (MRTR, sesión 2)

    @mcp.tool(
        title="Consultar",
        description=(
            "Ejecuta una consulta SQL de solo lectura sobre el dataset del curso y devuelve "
            "las primeras filas. Si la consulta escanea más datos de lo permitido, pide "
            "confirmación al usuario antes de ejecutarla."
        ),
    )
    async def consultar(sql: str, ctx: Context, maximo_filas: int = 50) -> list[dict[str, Any]]:
        if not bq.disponible():
            raise RuntimeError("Sin credenciales de BigQuery. Revisa el módulo 0 del notebook 1.")

        # Dry run primero: saber el coste antes de pagarlo. Este es el momento donde el
        # servidor descubre que necesita algo del usuario y no puede seguir solo.
        estimacion = bq.estimar(sql)

        if not estimacion.dentro_del_limite:
            respuesta = await ctx.elicit(
                message=(
                    f"Esta consulta escanearía {estimacion.megabytes:,.1f} MB, por encima del "
                    f"límite configurado. ¿Quieres ejecutarla igualmente?"
                ),
                schema=ConfirmacionDeGasto,
            )
            # El host puede aceptar, declinar o cancelar. Los tres casos son distintos y
            # el servidor tiene que distinguirlos.
            if respuesta.action != "accept" or not respuesta.data or not respuesta.data.continuar:
                raise RuntimeError(
                    f"Consulta cancelada por el usuario ({estimacion.megabytes:,.1f} MB estimados)."
                )

        return bq.consultar(sql, maximo_filas=maximo_filas)

    # ------------------------------------------------- Tool con progreso (sesión 2)

    @mcp.tool(
        title="Recorrer tablas",
        description=(
            "Recorre todas las tablas del dataset y devuelve cuántas columnas tiene cada una. "
            "Sirve para ver notificaciones de progreso en una operación larga."
        ),
    )
    async def recorrer_tablas(ctx: Context) -> dict[str, int]:
        if not bq.disponible():
            raise RuntimeError("Sin credenciales de BigQuery. Revisa el módulo 0 del notebook 1.")

        tablas = bq.listar_tablas()
        resultado: dict[str, int] = {}
        for indice, tabla in enumerate(tablas, start=1):
            await ctx.report_progress(
                progress=indice, total=len(tablas), message=f"Leyendo esquema de {tabla}"
            )
            resultado[tabla] = len(bq.describir_tabla(tabla))
        return resultado

    # ------------------------------------------------------------ Resources (sesión 2)

    @mcp.resource(
        "catalogo://tablas",
        title="Catálogo de tablas",
        description="Listado de tablas del dataset, para que el host lo traiga como contexto.",
        mime_type="text/markdown",
    )
    def catalogo() -> str:
        if not bq.disponible():
            return "# Catálogo\n\nSin credenciales de BigQuery."
        lineas = [f"# Dataset `{bq.PROYECTO_DATOS}.{bq.DATASET}`", ""]
        lineas += [f"- `{t}`" for t in bq.listar_tablas()]
        return "\n".join(lineas)

    @mcp.resource(
        "catalogo://tablas/{tabla}",
        title="Esquema de una tabla",
        description="Esquema de la tabla indicada, en Markdown.",
        mime_type="text/markdown",
    )
    def esquema(tabla: str) -> str:
        if not bq.disponible():
            return f"# {tabla}\n\nSin credenciales de BigQuery."
        filas = ["| Columna | Tipo | Modo |", "|---|---|---|"]
        filas += [f"| `{c['columna']}` | {c['tipo']} | {c['modo']} |" for c in bq.describir_tabla(tabla)]
        return f"# `{tabla}`\n\n" + "\n".join(filas)

    # -------------------------------------------------------------- Prompts (sesión 2)

    @mcp.prompt(
        title="Explorar una tabla",
        description="Workflow guiado para analizar una tabla del dataset desde cero.",
    )
    def explorar(tabla: str) -> str:
        return (
            f"Analiza la tabla `{tabla}` del dataset del curso.\n\n"
            f"1. Llama a `describir_tabla` para conocer su esquema.\n"
            f"2. Propón tres preguntas interesantes que se puedan responder con esas columnas.\n"
            f"3. Responde la primera con una consulta SQL, usando `consultar`.\n"
            f"4. Resume el hallazgo en dos frases, sin repetir la tabla de resultados."
        )

    return mcp
