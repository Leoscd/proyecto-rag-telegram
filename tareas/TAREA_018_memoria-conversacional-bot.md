# TAREA 018 — Memoria conversacional del bot (últimas 5 rondas, en memoria)

- Fecha asignada: 2026-05-19
- Fase del MVP: 2
- Estimación: ≤1 día
- Depende de: TAREA_017 (bot conversacional + fix tests)

## Objetivo
Que el bot de Telegram mantenga una conversación con contexto: recuerda las últimas 5 rondas (pregunta/respuesta) por usuario en memoria del proceso, las envía a la API en `/query`, y el prompt al LLM incluye ese historial cuando existe. Si no hay historial, el comportamiento es idéntico al actual.

## Contexto mínimo necesario
- Hoy el bot es stateless: cada mensaje es una consulta independiente (ver `src/bot/main.py :: handle_query`).
- El historial NO se persiste: vive solo en un dict del proceso del bot. Se pierde al reiniciar y eso es aceptable para el MVP (briefing: VPS 2GB/1vCPU, "nada de modelos locales pesados / todo intensivo a APIs externas"; sumar Supabase/Redis/archivos para esto sería overhead innecesario y está fuera de alcance).
- `QueryRequest` (`src/api/schemas.py`) hoy tiene `proyecto_id`, `mensaje`, `usuario_telegram`. El bot ya hace `POST /query` con esos 3 campos.
- `construir_prompt(query, chunks, similitud_umbral=0.35)` en `src/rag/prompt_builder.py` arma el prompt; hoy tiene el bloque `CONTEXTO:` y `PREGUNTA: {query}`. La rama `if not chunks:` (sin contexto) NO se toca.
- El cambio de proyecto se maneja en `proyecto_command` con `set_proyecto(user_id, proyecto_id)`.

## Archivos a crear / modificar
- `src/bot/main.py` — dict global de historial en memoria; agregar ronda tras cada respuesta exitosa; enviar historial en el `POST /query`; limpiar historial del usuario al cambiar de proyecto.
- `src/api/schemas.py` — agregar campo opcional `historial: list[dict] = []` a `QueryRequest`.
- `src/rag/prompt_builder.py` — incluir el historial en el prompt SOLO si viene no vacío.
- `tareas/resumenes/TAREA_018_resumen.md` — resumen de lo hecho.

## Contrato (inputs / outputs)

### `src/api/schemas.py`
En `QueryRequest`, agregar exactamente:
```python
historial: list[dict] = []
```
- Debe ser opcional con default `[]` (lista nueva por request, no mutable compartida — Pydantic ya lo maneja por campo; no usar default mutable a nivel de módulo).
- No tocar los otros campos ni el resto de schemas.

### `src/bot/main.py`
- Dict global a nivel de módulo, junto a `proyectos_activos`:
  ```python
  # Historial conversacional por usuario: {user_id: [{"pregunta": str, "respuesta": str}, ...]}
  historial: dict[int, list[dict]] = {}
  MAX_RONDAS = 5
  ```
- Helpers (firmas exactas):
  ```python
  def get_historial(user_id: int) -> list[dict]: ...        # devuelve [] si no hay
  def push_ronda(user_id: int, pregunta: str, respuesta: str) -> None: ...  # append y recorta FIFO a MAX_RONDAS
  def reset_historial(user_id: int) -> None: ...             # borra el historial del usuario
  ```
- En `handle_query`:
  - Al armar el `json=` del `POST /query`, agregar `"historial": get_historial(user_id)`.
  - Tras enviar una respuesta exitosa con contexto (la rama donde NO se hace `return` por `score < 0.4`), registrar la ronda con `push_ronda(user_id, mensaje, respuesta)`. La ronda guarda el texto de la respuesta del LLM (`respuesta`), no la imagen.
  - NO registrar ronda cuando `score < 0.4` (esa rama hace `return` antes; el "no encontré documentación" no es contexto útil).
  - NO registrar ronda en los `except` (timeout/error) ni cuando `response.status_code != 200`.
- En `proyecto_command`: en la rama donde se cambia de proyecto con éxito (`set_proyecto(...)` y se responde "Proyecto cambiado"), llamar `reset_historial(user_id)` para que el contexto no mezcle proyectos. No limpiar cuando solo se consulta el proyecto actual ni cuando el ID es inválido.

### `src/rag/prompt_builder.py`
- Cambiar la firma a:
  ```python
  def construir_prompt(
      query: str,
      chunks: list[ChunkRecuperado],
      similitud_umbral: float = 0.35,
      historial: list[dict] | None = None,
  ) -> tuple[str, bool]:
  ```
- `historial` opcional con default `None`. Tratar `None` como lista vacía.
- La rama `if not chunks:` (sin contexto) NO cambia: no inyectar historial ahí.
- Cuando hay chunks y `historial` NO está vacío, insertar el bloque ANTES de `CONTEXTO:`:
  ```
  HISTORIAL DE CONVERSACIÓN RECIENTE:
  Usuario: {ronda["pregunta"]}
  Asistente: {ronda["respuesta"]}
  ... (una por ronda, en orden cronológico, más vieja primero)

  CONTEXTO:
  {contexto}

  PREGUNTA ACTUAL: {query}

  RESPUESTA:
  ```
- Cuando `historial` está vacío: el prompt queda EXACTAMENTE como hoy (sin la sección de historial; mantené el texto `PREGUNTA: {query}` actual en ese caso — no cambiar a "PREGUNTA ACTUAL" si no hay historial, para no alterar el comportamiento existente).
- Defensa mínima: si una ronda no tiene las claves `pregunta`/`respuesta`, omitirla (no romper). No truncar ni recortar textos en el prompt builder (el límite de 5 rondas lo garantiza el bot).
- IMPORTANTE: identificar quién llama a `construir_prompt` (el endpoint `/query`) y pasarle `request.historial`. Si el llamador está en `src/rag/query.py`, ese archivo está en la lista de "NO modificar" salvo por esta única línea de paso de parámetro. Aclaración de alcance abajo.

## Criterios de aceptación
- [ ] `QueryRequest` acepta `historial` opcional; un `POST /query` SIN el campo `historial` sigue funcionando igual que antes (compatibilidad).
- [ ] El bot envía en `POST /query` el historial del usuario (hasta 5 rondas), en orden cronológico.
- [ ] Tras una respuesta con contexto, la ronda (pregunta + texto de respuesta) queda guardada para ese `user_id`; al llegar a 6 rondas, se descarta la más vieja (quedan 5).
- [ ] El historial NO se guarda en las ramas: `score < 0.4`, `status != 200`, timeout o excepción.
- [ ] `/proyecto <id>` con cambio exitoso limpia el historial del usuario; `/proyecto` (consulta) y `/proyecto abc` (inválido) NO lo limpian.
- [ ] El prompt incluye la sección "HISTORIAL DE CONVERSACIÓN RECIENTE:" SOLO cuando hay rondas; con historial vacío el prompt es idéntico al actual (incluida la línea `PREGUNTA: {query}`).
- [ ] La rama "sin chunks" de `construir_prompt` no cambió.
- [ ] El historial vive solo en memoria: no se escribió nada en Supabase, Redis ni archivos; la tabla `consultas` no cambió de schema.
- [ ] Solo se modificaron: `src/bot/main.py`, `src/api/schemas.py`, `src/rag/prompt_builder.py` y, como única excepción documentada, la línea del llamador de `construir_prompt` que pasa `historial`. Nada más.
- [ ] Existe `tareas/resumenes/TAREA_018_resumen.md` con qué se hizo y qué criterios se cumplieron.

## Cómo probar
1. Compatibilidad API (sin historial), con API levantada y `.env`:
   `curl -X POST $API_URL/query -H "Content-Type: application/json" -d '{"proyecto_id":1,"mensaje":"como se hace el revoque exterior","usuario_telegram":"test"}'`
   → responde igual que antes (no error de validación por el campo faltante).
2. Con historial:
   `curl -X POST $API_URL/query -H "Content-Type: application/json" -d '{"proyecto_id":1,"mensaje":"y el muro interior?","usuario_telegram":"test","historial":[{"pregunta":"como se construye el muro exterior","respuesta":"Segun los documentos disponibles, el muro exterior se ejecuta con mamposteria de ladrillo..."}]}'`
   → la respuesta interpreta "el muro interior" en relación a la pregunta previa (no responde como si "muro interior" fuera una consulta aislada sin sujeto).
3. Test manual del bot (VPS, bot corriendo):
   - Preguntar "¿cómo se hace el muro exterior?" → respuesta.
   - Luego "¿y el interior?" → el bot responde entendiendo que se habla de muros.
   - `/proyecto 2` → luego "¿y el interior?" → ya NO arrastra el contexto de muros (historial limpiado).
4. Reinicio: matar y relanzar el proceso del bot → el historial está vacío (esperado, aceptable).
5. Inspección de prompt: con un chunk dummy y `historial=[]`, `construir_prompt(...)` devuelve un prompt SIN "HISTORIAL DE CONVERSACIÓN RECIENTE"; con `historial=[{...}]` lo incluye antes de `CONTEXTO:`.

## Qué NO hacer
- NO persistir historial en Supabase, Redis ni archivos. NO cambiar el schema de `consultas`.
- NO modificar: `retriever.py`, `embedder.py`, `chunker.py`, `extractor.py`, `ingesta/`, `responder.py`, dashboard, tests existentes. La ÚNICA excepción permitida es UNA línea en el llamador de `construir_prompt` (probablemente `src/rag/query.py`) para pasar `request.historial`; si el cambio requiere más que pasar ese parámetro, parar y anotarlo, no refactorizar.
- NO subir el máximo de rondas por encima de 5 ni hacerlo configurable por env/feature flag.
- NO truncar/resumir respuestas con otra llamada al LLM ni agregar tokenizadores: el límite es por número de rondas.
- NO tocar `start`, `ayuda`, ni el formato de mensajes/imagen de `handle_query` definido en TAREA_017 (foto+caption, umbral 0.4, except de timeout/error).
- NO cambiar la línea `PREGUNTA: {query}` del caso sin historial.
- NO agregar dependencias nuevas.

## Notas para revisión
- Verificar que `historial` en `QueryRequest` es opcional y que un request viejo (sin el campo) NO da 422.
- Confirmar el recorte FIFO real: con 7 preguntas seguidas del mismo usuario, el historial enviado tiene exactamente las últimas 5, en orden cronológico (más vieja primero).
- Confirmar que `reset_historial` se llama SOLO en el cambio exitoso de proyecto.
- Confirmar que la rama `if not chunks:` de `prompt_builder.py` quedó intacta y que el caso "historial vacío" produce el prompt byte-idéntico al actual (incluido `PREGUNTA:` sin "ACTUAL").
- Edge: rondas con claves faltantes no deben romper el armado del prompt.
- Secrets: no se introdujo ningún secret nuevo; el dict de memoria no loguea contenido de conversaciones a stdout.
- Recursos VPS: 5 rondas × ~500 chars ≈ 2.5KB por usuario, sin límite de usuarios pero crecimiento despreciable para una demo; no se agregó proceso ni puerto nuevo; bot sigue en long polling.
- Revisar que el llamador de `construir_prompt` solo sumó el paso de `historial` y no se "mejoró de paso" `query.py`.
