# Curso MCP · servidores remotos

Curso práctico de **Model Context Protocol** centrado en servidores remotos: qué es MCP, qué
primitivas ofrece, para qué sirve cada una y cómo se usan —siempre desde el lado servidor y
desde el lado cliente— y después las extensiones del protocolo con casos de uso reales.

**4 sesiones de 2 horas · 4 notebooks · 8 horas lectivas**

| | Decisión |
|---|---|
| **Especificación** | `2026-07-28` |
| **SDK** | [`mcp` 2.0.0](https://github.com/modelcontextprotocol/python-sdk) (Python ≥3.10) |
| **Se explica en** | Google Colab |
| **Se ejecuta en** | Cloud Run |
| **Datos de ejemplo** | BigQuery (dataset público) |
| **Transporte** | Streamable HTTP |

> **Remoto de principio a fin.** Nada de stdio, nada de servidor dentro del notebook, nada de
> localhost. Desde el primer módulo el servidor vive en Cloud Run con URL pública y el Colab
> es siempre el lado cliente. Ningún patrón que se aprenda aquí es desechable.

---

## Los notebooks

| # | Sesión | Contenido | Abrir |
|---|---|---|---|
| 1 | **Fundamentos** | Qué es MCP · el protocolo a mano con `httpx` · `server/discover` · despliegue a Cloud Run · **tools** | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/noelserdna/curso-mcp/blob/main/notebooks/01-fundamentos.ipynb) |
| 2 | **Primitivas** | **Resources** y plantillas de URI · `ttlMs`/`cacheScope` · **prompts** · **interacción** a mitad de llamada · **progreso** y suscripciones | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/noelserdna/curso-mcp/blob/main/notebooks/02-primitivas.ipynb) |
| 3 | **Auth** | Por qué authless no vale · OAuth en MCP y CIMD · verificación de tokens · **el puente de identidad a BigQuery** | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/noelserdna/curso-mcp/blob/main/notebooks/03-auth.ipynb) |
| 4 | **Extensiones** | Negociación de extensiones · extensiones de auth · **MCP Apps** con widget · escribir la tuya · producción | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/noelserdna/curso-mcp/blob/main/notebooks/04-extensiones.ipynb) |

El temario detallado, con minutado por bloque, está en [`TEMARIO.md`](TEMARIO.md).

---

## Requisitos

Antes de la primera sesión, cada alumno necesita:

- Un **proyecto de Google Cloud con facturación activada**. Sin esto la sesión 1 no da tiempo.
- Cuenta de Google para Colab.
- Nociones de Python. No hace falta saber MCP ni haber tocado BigQuery.

Las consultas van contra un dataset público (`bigquery-public-data`), así que no hay que
cargar datos: solo un proyecto donde facturar el escaneo, que en los ejemplos del curso es de
céntimos.

---

## Cómo está montado

```
curso_mcp/                  Paquete del curso, importado por los notebooks
├── server.py               El servidor MCP: tools, resources, prompts, interacción
├── bq.py                   Acceso a BigQuery, con dry run y límite de escaneo
├── widget.py               Extensión MCP Apps y el HTML del widget
└── extension_auditoria.py  Una extensión propia, escrita desde cero
deploy/                     Lo necesario para Cloud Run
├── main.py                 Punto de entrada ASGI
├── Dockerfile
└── requirements.txt
notebooks/                  Un notebook por sesión
```

**Un solo despliegue para todo el curso.** El servicio que se sube en la sesión 1 ya contiene
el código de las cuatro, y cada sesión activa y consume la parte que le toca. Así se conserva
el enfoque remoto sin pagar un par de minutos de despliegue en cada iteración, que con 8 horas
lectivas sería inasumible.

### Probarlo en local sin desplegar

El servidor se puede recorrer entero en memoria, sin Cloud Run y sin credenciales — los tools
que necesitan BigQuery devuelven un error legible en vez de reventar:

```bash
pip install "mcp==2.0.0"
python -c "
import asyncio
from mcp import Client
from curso_mcp.server import crear_servidor

async def main():
    async with Client(crear_servidor()) as c:
        print([t.name for t in (await c.list_tools()).tools])

asyncio.run(main())
"
```

### Desplegar

```bash
gcloud run deploy curso-mcp --source . --region europe-west1 --allow-unauthenticated
```

`--allow-unauthenticated` es deliberado y **temporal**: la sesión 3 cierra la puerta.

---

## Material de ampliación

Fuera de las 8 horas lectivas, para hacer por cuenta propia contra el mismo servidor:

- **Implementar la extensión Tasks** desde su especificación. No viene en el SDK 2.0.0, así que
  se escribe entera. Es el mejor ejercicio del temario.
- **Patrón `search` + `execute`** cuando la superficie pasa de quince acciones.
- **Paginación y presupuesto de payload** para consultas que devuelven más de lo que cabe.
- **Protección del servicio**: cuotas, abuso y control de gasto en BigQuery.

---

## Referencias

- [Especificación `2026-07-28`](https://modelcontextprotocol.io/specification/2026-07-28/)
- [Extensiones oficiales](https://modelcontextprotocol.io/extensions/overview)
- [Matriz de soporte por cliente](https://modelcontextprotocol.io/extensions/client-matrix)
- [SDK de Python](https://github.com/modelcontextprotocol/python-sdk)
