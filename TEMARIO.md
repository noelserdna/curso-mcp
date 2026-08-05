# Curso MCP — servidores remotos

**4 sesiones de 2 horas · 4 notebooks · 8 horas lectivas**

Curso sobre Model Context Protocol centrado en servidores remotos: qué es MCP, qué primitivas
ofrece, para qué sirve cada una y cómo se usan —siempre con el lado servidor y el lado
cliente— y después las extensiones del protocolo con casos de uso reales.

## Premisas

| Decisión | Valor |
|---|---|
| Spec | `2026-07-28` |
| SDK | `mcp` 2.0.0 (Python ≥3.10) — MCP Apps in-core, extensiones SEP-2133 |
| Explicación | Colab |
| Ejecución | Cloud Run |
| Datos de ejemplo | BigQuery |
| Transporte | Streamable HTTP, y solo eso |

**Remoto de principio a fin.** Nada de stdio, nada de servidor en el kernel del notebook,
nada de localhost. El servidor vive en Cloud Run con URL pública, y el Colab es siempre el
lado cliente.

## Qué hace posible que esto quepa en 8 horas

Con este presupuesto el alumno **no construye el servidor línea a línea: lo lee, lo despliega,
lo consume y lo modifica en puntos acotados**. El código viene escrito en un paquete del curso
instalable con `pip`; las celdas ejecutan y explican, y en cada módulo hay dos o tres huecos
concretos donde el alumno interviene. Escribir desde cero es lo primero que hay que sacrificar,
porque es lo que más tiempo consume y menos concepto transmite por minuto.

**Un solo despliegue, en la sesión 1.** El servicio que se sube ya contiene el código de las
cuatro sesiones; cada módulo activa y consume la parte que le toca. Así se conserva el enfoque
remoto sin pagar uno o dos minutos de deploy por cada iteración —lo que en 8 horas sería
inasumible— y el alumno sigue teniendo su propia URL pública desde el primer día.

**Presupuesto real:** de 120 minutos por sesión, unos 90 de contenido efectivo.

---

## Sesión 1 — Qué es MCP y tu primer servidor remoto

*Notebook `01-fundamentos.ipynb`*

| Bloque | Min |
|---|:--:|
| **Qué es MCP y por qué existe.** El problema del integrador por cada modelo y cada IDE. Arquitectura host / cliente / servidor: quién habla con quién y quién decide qué. Por qué remoto y no local | 20 |
| **El protocolo por dentro.** Un cliente a mano con `httpx` contra una URL real: JSON-RPC sobre Streamable HTTP, `server/discover`, `_meta` (`protocolVersion`, `clientCapabilities`, `clientInfo`), `resultType`. Por qué es stateless y qué gana con ello en Cloud Run | 25 |
| **Despliegue.** Proyecto GCP, servidor del curso a Cloud Run, URL pública viva, `Client` del SDK llamándola desde Colab. El único deploy del curso | 25 |
| **Tools.** La primitiva central. Servidor: `@mcp.tool`, esquemas de entrada y salida, errores. Cliente: `tools/list`, `tools/call`. Ejemplo sobre BigQuery: listar tablas, describir esquema, consultar. Por qué el diseño del schema se paga en tokens y en aciertos | 40 |

## Sesión 2 — El resto de primitivas

*Notebook `02-primitivas.ipynb`*

| Bloque | Min |
|---|:--:|
| **Resources.** Datos y documentos como contexto navegable que trae el host, no que invoca el modelo: cuándo elegir esto y cuándo un tool. Servidor: resources y plantillas de URI. Cliente: `resources/list`, `resources/read`. `ttlMs` y `cacheScope`, que aquí son diseño y no adorno porque cada lectura contra BigQuery cuesta dinero | 30 |
| **Prompts.** Workflows enlatados que dispara el usuario, no el modelo. Servidor: prompts con argumentos. Cliente: `prompts/list`, `prompts/get` y cómo los expone el host. Ejemplo: análisis que ya sabe qué tablas cruzar | 20 |
| **Interacción.** Cuando un tool no puede resolverse de una pasada. `InputRequiredResult` con `inputRequests`, reintento del cliente con `inputResponses`, contexto entre vueltas con `requestState`. Ejemplo: confirmar una consulta cara antes de lanzarla | 25 |
| **Progreso y suscripciones.** `notifications/progress` en el flujo de la petición y `subscriptions/listen` para cambios. Realidad de Cloud Run: 5 min por defecto, 60 de máximo, y por encima de 15 hay que asumir reconexión del cliente | 20 |

## Sesión 3 — Autenticación y autorización

*Notebook `03-auth.ipynb`*

| Bloque | Min |
|---|:--:|
| **Por qué authless deja de valer** en cuanto hay algo que proteger, y qué expone realmente un servidor abierto a internet | 15 |
| **OAuth en MCP.** Client ID Metadata Documents como vía preferente. Servidor: metadata del recurso protegido, validación de token, middleware. Cliente: descubrir el servidor de autorización, obtener y renovar credenciales | 40 |
| **El puente a GCP.** Cómo la identidad de un usuario externo se traduce en permisos reales sobre BigQuery, sin que el servidor acabe siendo una llave maestra. La parte que no está escrita en ningún sitio | 35 |

## Sesión 4 — Extensiones

*Notebook `04-extensiones.ipynb`*

| Bloque | Min |
|---|:--:|
| **Qué es una extensión.** Qué queda dentro y fuera del core, identificadores con prefijo de proveedor, y la negociación: el cliente las declara en `clientCapabilities.extensions`, el servidor en `server/discover`. Degradación elegante cuando el otro lado no la soporta | 20 |
| **Extensiones de autorización.** `oauth-client-credentials` para máquina a máquina sin navegador — el caso natural de un servicio que consulta BigQuery por su cuenta. Mención de `enterprise-managed-authorization` | 20 |
| **MCP Apps.** `io.modelcontextprotocol/ui`, incluida en el SDK de Python sin npm. Servidor: `Apps()`, recurso `ui://` asociado a un tool. Widget que presenta una consulta a BigQuery como tabla y gráfico, visto en Claude Desktop. Caída a texto cuando el host no la soporta | 35 |
| **Cierre: llevarlo a producción.** Observabilidad con el OpenTelemetry del SDK. Límites que muerden: 4 MiB de cuerpo, y los hosts truncan resultados. Publicación en el directorio de conectores | 15 |

---

## Qué queda fuera, y dónde va

Estas piezas no caben en 8 horas lectivas. Van como **notebooks de ampliación** que el alumno
ejecuta por su cuenta, con el mismo servidor ya desplegado:

- **Construir tu propia extensión**, implementando Tasks desde la especificación — no viene en
  el SDK, así que se escribe entera. Es el mejor ejercicio del temario y el que más tiempo
  pide; como material asíncrono no se pierde.
- **Diseño de superficie**: search+execute cuando hay decenas de operaciones, y cómo carvar
  tools para una API grande.
- **Presupuesto de payload y paginación** cuando la consulta devuelve más de lo que cabe.
- **Protección de un servicio expuesto**: cuotas, abuso y control del coste de BigQuery.

## Pendiente de decidir

1. **Dataset del hilo conductor**: uno público de BigQuery (arranque inmediato, cero setup) o
   uno que el alumno cargue antes de empezar.
2. **Cuánto BigQuery se explica**: si el alumno llega sabiendo BQ y aquí solo se consume, o hay
   que enseñar lo justo para sostener los ejemplos.
3. **Nivel de partida en GCP**: si el proyecto y la facturación vienen resueltos de casa o el
   setup entra dentro de los 25 minutos de la sesión 1.
