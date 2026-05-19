# Resumen TAREA 018 — Memoria conversacional del bot

## Qué se implementó

### 1. `src/api/schemas.py`
- Agregado campo opcional `historial: list[dict] = []` a `QueryRequest`
- Compatible hacia atrás: requests sin `historial` funcionan igual que antes

### 2. `src/rag/prompt_builder.py`
- Nueva firma: `construir_prompt(..., historial: list[dict] | None = None)`
- Si `historial` tiene rondas válidas, inserta bloque **"HISTORIAL DE CONVERSACIÓN RECIENTE:"** antes de `CONTEXTO:`
- Usa `"PREGUNTA ACTUAL:"` cuando hay historial, `"PREGUNTA:"` cuando no lo hay (mantiene comportamiento anterior)
- Defensa: omite rondas sin claves `pregunta`/`respuesta`

### 3. `src/api/routes/query.py`
- Una línea: pasa `historial=request.historial` a `construir_prompt()`

### 4. `src/bot/main.py`
- Agregados:
  - `historial: dict[int, list[dict]] = {}` global
  - `MAX_RONDAS = 5`
  - `get_historial(user_id)` → devuelve `[]` si no hay
  - `push_ronda(user_id, pregunta, respuesta)` → append y recorta FIFO
  - `reset_historial(user_id)` → limpia historial
- En `handle_query`: envía `historial` en el POST y guarda ronda tras respuesta exitosa (score >= 0.4)
- En `proyecto_command`: limpia historial al cambiar exitosamente de proyecto

## Decisiones tomadas
- Historial en memoria (no persistence) según briefing MVP (VPS 2GB/1vCPU)
- Máximo 5 rondas para noinflar prompt
- Solo guardar ronda cuando hay contexto útil (score >= 0.4)
- Resetear historial al cambiar de proyecto para no mezclar contextos

## Problemas encontrados
- Ninguno; implementación directa согласно spec

## Qué quedó fuera de scope
- Persistencia en Supabase/Redis
- Tests unitarios de historial (no se pediu)
- Historial por proyecto (solo por usuario)

## Cómo probarlo
```bash
# 1. API sin historial (compatibilidad)
curl -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id":1,"mensaje":"test","usuario_telegram":"test"}'

# 2. API con historial
curl -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id":1,"mensaje":"y el interior?","usuario_telegram":"test","historial":[{"pregunta":"como se hace el muro exterior","respuesta":"Con ladrillo..."}]}'
```

## Criteria cumplidos
- [x] QueryRequest acepta historial opcional
- [x] Bot envía hasta 5 rondas en orden cronológico
- [x] Push guarda ronda tras respuesta exitosa (score >= 0.4)
- [x] No guarda ronda en score < 0.4, status != 200, timeout, exception
- [x] /proyecto <id> con cambio exitoso limpia historial
- [x] Prompt incluye historial SOLO cuando hay rondas
- [x] Rama "sin chunks" intacta
- [x] Solo se modificaron los 4 archivos especificados