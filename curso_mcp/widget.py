"""MCP Apps: un widget que enseña el resultado de una consulta dentro de la conversación.

La extensión `io.modelcontextprotocol/ui` viene incluida en el SDK de Python, así que no
hace falta npm ni un build de frontend: el widget es un HTML que el servidor sirve como
recurso `ui://` y que el host renderiza en un iframe.

Regla que el curso repite en la sesión 4: una extensión es siempre opcional, así que el
tool tiene que devolver algo con sentido aunque el host no sepa renderizar nada.
"""

from __future__ import annotations

from typing import Any

from mcp.server.apps import Apps
from mcp.server.mcpserver import Context

from curso_mcp import bq

URI_WIDGET = "ui://curso-mcp/tabla.html"

HTML_WIDGET = """
<!doctype html>
<meta charset="utf-8">
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.5 system-ui, sans-serif; margin: 0; padding: 12px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent); }
  th { font-weight: 600; position: sticky; top: 0; background: Canvas; }
  .envoltorio { max-height: 340px; overflow: auto; }
  .vacio { opacity: .6; padding: 24px; text-align: center; }
</style>
<div id="salida" class="vacio">Esperando datos…</div>
<script type="module">
  // El host entrega los datos del tool al iframe. Mientras no lleguen, el widget
  // enseña su estado vacío en vez de una pantalla en blanco.
  const salida = document.getElementById('salida');

  function pintar(filas) {
    if (!Array.isArray(filas) || filas.length === 0) {
      salida.className = 'vacio';
      salida.textContent = 'La consulta no devolvió filas.';
      return;
    }
    const columnas = Object.keys(filas[0]);
    const cabecera = columnas.map((c) => `<th>${c}</th>`).join('');
    const cuerpo = filas
      .map((f) => `<tr>${columnas.map((c) => `<td>${f[c] ?? ''}</td>`).join('')}</tr>`)
      .join('');
    salida.className = 'envoltorio';
    salida.innerHTML = `<table><thead><tr>${cabecera}</tr></thead><tbody>${cuerpo}</tbody></table>`;
  }

  window.addEventListener('message', (evento) => {
    const datos = evento.data?.structuredContent ?? evento.data;
    if (datos?.filas) pintar(datos.filas);
  });
</script>
"""


def construir_extension_apps() -> Apps:
    """Devuelve la extensión MCP Apps con su tool y su recurso de UI."""
    apps = Apps()

    @apps.tool(
        resource_uri=URI_WIDGET,
        title="Consultar con tabla",
        description=(
            "Ejecuta una consulta SQL sobre el dataset del curso y presenta el resultado "
            "como tabla navegable cuando el host soporta interfaces; en caso contrario "
            "devuelve el mismo resultado en texto."
        ),
    )
    def consultar_con_tabla(sql: str, ctx: Context, maximo_filas: int = 50) -> dict[str, Any]:
        if not bq.disponible():
            raise RuntimeError("Sin credenciales de BigQuery. Revisa el módulo 0 del notebook 1.")
        filas = bq.consultar(sql, maximo_filas=maximo_filas)
        # El mismo payload sirve al widget (que lee `filas`) y al host que solo muestra
        # texto: la degradación no es una rama aparte, es devolver datos bien formados.
        return {"filas": filas, "total": len(filas)}

    apps.add_html_resource(URI_WIDGET, HTML_WIDGET)
    return apps
