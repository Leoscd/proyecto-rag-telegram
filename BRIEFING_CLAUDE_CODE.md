# BRIEFING — Sistema RAG Operativo para Obras de Construccion

## Contexto del proyecto

Quiero construir un sistema de inteligencia operativa para proyectos de construccion e infraestructura. El sistema tiene dos tipos de usuarios:

- **Jefe de obra / administrador**: carga documentos del proyecto (planos, manuales, especificaciones, cronogramas) desde un panel web
- **Operario en campo**: consulta informacion desde Telegram usando lenguaje natural, desde cualquier lugar (obras remotas, mineras, rutas, con internet satelital)

El problema que resuelve: hoy la informacion critica de una obra (planos, guias de ejecucion, protocolos de seguridad) no llega a tiempo ni en forma al operario que la necesita en campo. Esto genera errores, accidentes y retrasos. El 70% de los proyectos de construccion sufren retrasos por falta de coordinacion.

---

## Lo que debe hacer el sistema

### Panel de administracion (web)
- Subir documentos por proyecto: PDFs, imagenes de planos, manuales Word
- Asignar metadata a cada documento: proyecto, sector, tipo (plano / manual / especificacion / protocolo seguridad / cronograma)
- El sistema procesa el documento, extrae texto, genera embeddings y lo guarda en la base de conocimiento
- Los planos se guardan como imagen + texto del rotulo (numero de plano, especialidad, sector, escala, fecha)

### Bot de Telegram (campo)
- El operario envia un mensaje en lenguaje natural: "como se hace el revoque exterior en el sector norte" o "protocolo de seguridad para trabajo en altura"
- El sistema busca en la base de conocimiento los fragmentos mas relevantes
- Responde con texto claro + imagen del plano o detalle si corresponde
- Registra cada consulta para control de calidad

### Dashboard de control (web)
- Muestra todas las consultas realizadas
- Muestra que documentos se usaron para responder
- Muestra el score de similitud (para detectar cuando el sistema no encontro buena informacion)
- Permite identificar preguntas frecuentes sin respuesta → gap de documentacion

---

## Stack tecnico definido

| Componente | Tecnologia |
|------------|-----------|
| Backend API | FastAPI (Python) |
| Bot mensajeria | Telegram Bot API (python-telegram-bot) |
| Embeddings | OpenAI text-embedding-3-large |
| LLM respuesta | MiniMax API (endpoint chat) |
| Base vectorial | Supabase pgvector |
| Storage archivos | Supabase Storage |
| Logs y metadata | Supabase PostgreSQL |
| Frontend admin + dashboard | HTML + CSS + JS vanilla (sin frameworks) |
| Deploy | VPS Linux (2GB RAM / 1vCPU) con systemd |

Restriccion importante: el VPS tiene recursos limitados. Nada de modelos locales pesados. Todo procesamiento intensivo va a APIs externas.

---

## Estructura de datos principal

### Tabla `proyectos`
- id, nombre, descripcion, fecha_inicio, activo

### Tabla `documentos`
- id, proyecto_id, nombre, tipo, sector, ruta_archivo, texto_extraido, fecha_carga

### Tabla `chunks` (pgvector)
- id, documento_id, proyecto_id, texto, embedding (vector 3072), metadata JSON

### Tabla `consultas`
- id, proyecto_id, usuario_telegram, mensaje_original, respuesta_generada, chunks_usados (array), score_maximo, timestamp

---

## Tipos de documentos que ingresaran

1. **Manuales de seguridad laboral** — PDF texto, secciones claras (trabajo en altura, excavaciones, instalaciones electricas, espacios confinados)
2. **Especificaciones tecnicas** — PDF texto con tablas y referencias a planos
3. **Planos** — PDF o imagen con rotulo. El rotulo contiene: numero, nombre proyecto, especialidad, sector, escala, fecha, firma
4. **Cronogramas de obra** — Excel o tabla con tareas, fechas, responsables, costo estimado
5. **Protocolos de procedimiento** — PDF texto con pasos de ejecucion de tareas

---

## Flujo RAG detallado

```
INGESTA:
documento → extraccion texto (PyMuPDF / python-docx) →
chunking con overlap (500 tokens, 50 overlap) →
embedding OpenAI → guardar en Supabase pgvector + metadata

CONSULTA:
mensaje operario → embedding OpenAI →
busqueda similitud coseno en Supabase (top 5 chunks) →
construir prompt con contexto →
MiniMax genera respuesta →
si chunk tiene plano asociado → adjuntar imagen →
respuesta texto + imagen a Telegram →
log en tabla consultas
```

---

## Estructura de carpetas esperada

```
rag-obras/
├── CLAUDE.md
├── .env.example
├── requirements.txt
├── skills/
│   ├── ingesta/SKILL.md
│   ├── rag-query/SKILL.md
│   ├── telegram-bot/SKILL.md
│   └── dashboard/SKILL.md
├── src/
│   ├── ingesta/
│   │   ├── extractor.py       # extrae texto de PDF, Word, imagen
│   │   ├── chunker.py         # divide en chunks con metadata
│   │   └── embedder.py        # genera embeddings y guarda en Supabase
│   ├── rag/
│   │   ├── retriever.py       # busqueda vectorial en Supabase
│   │   ├── prompt_builder.py  # construye contexto para LLM
│   │   └── responder.py       # llama MiniMax y formatea respuesta
│   ├── bot/
│   │   ├── main.py            # entry point del bot Telegram
│   │   ├── handlers.py        # maneja mensajes entrantes
│   │   └── formatter.py       # formatea respuesta para Telegram
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   ├── routes/
│   │   │   ├── ingest.py      # POST /ingest
│   │   │   ├── query.py       # POST /query
│   │   │   └── logs.py        # GET /logs
│   │   └── schemas.py         # modelos Pydantic
│   └── dashboard/
│       ├── index.html         # dashboard control calidad RAG
│       └── admin.html         # panel carga de documentos
├── data/
│   └── demo/                  # documentos de prueba para demo TIIC
└── tests/
    ├── test_ingesta.py
    ├── test_rag.py
    └── test_bot.py
```

---

## Variables de entorno necesarias

```
OPENAI_API_KEY=
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
SUPABASE_URL=
SUPABASE_KEY=
TELEGRAM_BOT_TOKEN=
```

---

## Prioridad de desarrollo (MVP para demo)

**Fase 1 — Core RAG funcional**
- Ingesta de PDFs texto
- Embeddings + guardado en Supabase
- Query basico que devuelve texto

**Fase 2 — Bot funcional**
- Telegram recibe mensaje → llama API → devuelve respuesta texto
- Soporte de imagen en respuesta

**Fase 3 — Panel admin y dashboard**
- Formulario subida de documentos
- Dashboard con logs de consultas

**Fase 4 — Pulido para demo**
- Datos reales cargados (manuales seguridad, planos con rotulo, cronograma)
- Demo end-to-end grabado en video

---

## Caso de uso demo para el pitch TIIC

Proyecto ficticio o real de mediana escala.
El operario envia por Telegram: *"estoy por arrancar el encofrado de columnas, que tengo que revisar antes"*
El sistema responde:
- Texto: pasos de verificacion previa al encofrado segun especificacion tecnica
- Imagen: plano de detalle de columna del sector correspondiente
- Texto adicional: advertencias de seguridad para trabajo con encofrados

Eso es lo que el jurado de TIIC tiene que ver funcionando en vivo o en video.

---

## Lo que NO entra en el MVP

- Autenticacion de usuarios (se agrega despues)
- Multiproyecto con permisos por rol (se agrega despues)
- Actualizacion de cronograma desde el bot (Fase 2 del producto)
- Integracion con arch-proposal-suite (modulo separado, se integra despues)

---

*Fecha limite demo: 22 mayo 2026*
*Responsable: Leonardo Diaz — SoyLeo AI*
*Colaborador codigo: [nombre]*
