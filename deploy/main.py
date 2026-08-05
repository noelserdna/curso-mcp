"""Punto de entrada del servidor en Cloud Run.

Cloud Run inyecta el puerto en la variable de entorno PORT y espera un servidor HTTP
escuchando en 0.0.0.0. El SDK devuelve una aplicación ASGI de Starlette, así que basta
con servirla con uvicorn.
"""

import os

import uvicorn

from curso_mcp.server import crear_servidor

mcp = crear_servidor()

# `host="0.0.0.0"` es obligatorio en Cloud Run: el valor por defecto del SDK es
# 127.0.0.1 y el contenedor quedaría inalcanzable desde fuera.
app = mcp.streamable_http_app(streamable_http_path="/mcp", host="0.0.0.0")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
