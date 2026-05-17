# TAREA 009 — Bot Telegram completo

- Fecha asignada: 2026-05-17
- Fase del MVP: 2 — Bot funcional
- Estimación: ≤ 1 día
- Depende de: TAREA 008 (API correcta y levantada)

## Objetivo
Completar y corregir el bot de Telegram para que el operario pueda consultar desde el campo. El esqueleto en `src/bot/main.py` existe pero tiene bugs y falta el envío de imágenes correctamente.

## Qué tiene bugs en el bot actual (src/bot/main.py)

1. `proyecto_id = 1` hardcodeado — agregar comando `/proyecto <id>` para cambiar proyecto activo por usuario
2. `{API_URL}/storage/documentos/{ruta_imagen}` no existe — la API debe generar la URL firmada de Supabase Storage
3. `except: pass` (bare except) — manejar errores con mensaje al usuario
4. Sin `__init__.py` en `src/bot/`

## Archivos a crear / modificar

- `src/bot/main.py` — corregir y completar
- `src/bot/__init__.py` — vacío
- `src/api/routes/storage.py` — nuevo endpoint GET /storage/url
- `src/api/main.py` — registrar el router de storage

## Contrato

### Nuevo endpoint GET /storage/url

```
GET /storage/url?path={ruta_archivo}
```

Genera una URL firmada de Supabase Storage válida por 1 hora:

```python
result = supabase_client.storage.from_("documentos").create_signed_url(
    path=path,
    expires_in=3600,
)
return {"url": result["signedURL"]}
```

Response:
```json
{ "url": "https://xesbkiqnknrzqzbvymcf.supabase.co/storage/v1/...?token=..." }
```

### Comandos del bot

| Comando | Acción |
|---|---|
| `/start` | Mensaje de bienvenida con instrucciones |
| `/proyecto <id>` | Cambiar proyecto activo (por defecto proyecto 1) |
| `/proyecto` (sin id) | Mostrar proyecto activo actual |
| Mensaje de texto | Consulta RAG → respuesta texto + imagen si aplica |

### Flujo de consulta con imagen

```python
# 1. POST /query → obtener respuesta
data = await client.post(f"{API_URL}/query", json={...})

# 2. Si tiene_imagen=True y ruta_imagen → pedir URL firmada
if data["tiene_imagen"] and data["ruta_imagen"]:
    url_resp = await client.get(f"{API_URL}/storage/url",
                                params={"path": data["ruta_imagen"]})
    url_imagen = url_resp.json()["url"]
    # 3. Descargar imagen y enviar al usuario
    img_bytes = (await client.get(url_imagen)).content
    await update.message.reply_photo(img_bytes)
```

### Gestión del proyecto activo por usuario

Usar un dict en memoria `proyectos_activos: dict[int, int]` donde la clave es `user.id` de Telegram y el valor es el `proyecto_id`. Default: 1.

```python
proyectos_activos: dict[int, int] = {}

def get_proyecto(user_id: int) -> int:
    return proyectos_activos.get(user_id, 1)
```

### Formato de respuesta al operario

```
🔎 *Buscando en los documentos...*

[respuesta de MiniMax]

📊 Relevancia: 87%  (= score_maximo * 100, redondeado)
```

Si `score_maximo < 0.4` (contexto pobre):
```
⚠️ No encontré documentación específica sobre esto.
```

## Criterios de aceptación
- [ ] `/start` responde con bienvenida
- [ ] `/proyecto 2` cambia el proyecto activo; `/proyecto` sin args muestra el activo
- [ ] Mensaje de texto → consulta RAG → respuesta texto en ≤ 35 segundos
- [ ] Si hay imagen → se adjunta la foto después del texto
- [ ] Si score bajo → mensaje de advertencia en vez de respuesta inventada
- [ ] Timeout de 30s → mensaje de error claro, no crash
- [ ] `python -m src.bot.main` arranca sin errores (con `TELEGRAM_BOT_TOKEN` en .env)

## Cómo probar
```bash
# Levantar la API en terminal 1
uvicorn src.api.main:app --port 8000

# Levantar el bot en terminal 2 (requiere TELEGRAM_BOT_TOKEN en .env)
python -m src.bot.main

# Probar en Telegram:
# /start
# /proyecto 1
# "protocolo de seguridad para trabajo en altura"
```

## Qué NO hacer
- Sin multiproyecto con permisos (autenticación fuera del MVP)
- Sin historial de conversación — cada mensaje es independiente
- Sin webhook — usar long polling siempre
- Sin base de datos para persistir proyecto activo (dict en memoria alcanza para demo)

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_009_resumen.md`:

```markdown
# Resumen TAREA 009

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Prueba realizada en Telegram
- Consulta enviada: [texto]
- Respuesta recibida: [sí/no, primeras 100 chars]
- Imagen adjunta: [sí/no]
- Score mostrado: [valor]
## Cómo probarlo
```
