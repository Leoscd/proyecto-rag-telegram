# Resumen Tareas 2 y 3

## Tarea 2: Bot Telegram
### Qué se implementó
- `src/bot/main.py` — Bot con python-telegram-bot
- handlers: /start, /help, /logs, consulta texto libre
- Integración con `/query` endpoint de la API
- Soporte para adjuntar imágenes si `tiene_imagen=True`

## Tarea 3: Dashboard
### Qué se implementó
- `src/dashboard/index.html` — Dashboard completo vanilla
- Tabla de consultas recientes con scores codificados por color
- Stats: total consultas, score promedio
- Formulario para subir documentos via `/ingest`
- Auto-refresh cada 30s

##部署
```bash
# API
uvicorn src.api.main:app --port 8000

# Bot (en otro terminal)
python -m src.bot.main

# Dashboard
# Acceder a http://localhost:8000/src/dashboard/index.html
# O servir static:
python -m http.server 8080 --directory src/dashboard
```

## Problemas encontrados
- Ninguno significativo

## Pendiente
- Tests de integración con APIs reales
- Autenticación (fuera del MVP)