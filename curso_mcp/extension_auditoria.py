"""Una extensión propia, escrita desde cero (sesión 4).

Registra cada `tools/call` que atraviesa el servidor y añade un método nuevo al protocolo
para consultar ese registro. Es deliberadamente pequeña, pero toca las tres cosas que
hacen falta para entender el mecanismo:

  1. **Identificador con prefijo propio.** Nadie más puede colisionar con él.
  2. **Un interceptor de `tools/call`**, que es el único punto donde una extensión puede
     envolver el core.
  3. **Un método nuevo**, `com.codecrypto.academy/auditoria.listar`, que solo existe si el
     servidor carga esta extensión.

La regla de oro está en el punto 3: un cliente que no negocie la extensión no sabe que ese
método existe, así que la extensión no puede ser obligatoria para usar el servidor. Lo que
aporta es aditivo, y lo que intercepta deja pasar todo lo que no le incumbe.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from mcp.server.extension import Extension, MethodBinding
from pydantic import BaseModel

IDENTIFICADOR = "com.codecrypto.academy/auditoria"


@dataclass
class Anotacion:
    herramienta: str
    argumentos: dict[str, Any]


class ParamsListar(BaseModel):
    """Parámetros del método nuevo. Vacío: se piden todas las anotaciones."""

    limite: int = 20


@dataclass
class Auditoria(Extension):
    """Lleva un registro en memoria de los tools invocados."""

    identifier: str = IDENTIFICADOR
    anotaciones: list[Anotacion] = field(default_factory=list)

    def settings(self) -> dict[str, Any]:
        # Lo que aquí se devuelva aparece en `capabilities.extensions[identificador]`
        # dentro de la respuesta de `server/discover`. Es la ficha técnica que el
        # cliente lee para decidir si sabe hablar con esta extensión.
        return {"persistente": False, "limiteRegistro": 200}

    async def intercept_tool_call(self, params, ctx, call_next):  # type: ignore[no-untyped-def]
        self.anotaciones.append(Anotacion(herramienta=params.name, argumentos=dict(params.arguments or {})))
        del self.anotaciones[:-200]
        # Pasar la llamada intacta: interceptar no es secuestrar.
        return await call_next(ctx)

    def methods(self) -> Sequence[MethodBinding]:
        async def listar(params: ParamsListar, ctx: Any) -> dict[str, Any]:
            recientes = self.anotaciones[-params.limite :]
            return {
                "total": len(self.anotaciones),
                "anotaciones": [
                    {"herramienta": a.herramienta, "argumentos": a.argumentos} for a in recientes
                ],
            }

        return (
            MethodBinding(
                method=f"{IDENTIFICADOR}.listar",
                params_type=ParamsListar,
                handler=listar,
                protocol_versions=None,
            ),
        )
