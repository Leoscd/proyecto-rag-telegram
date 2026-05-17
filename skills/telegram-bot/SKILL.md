# Skill: Telegram Bot para RAG-Obras

## Descripción
Bot de Telegram que conecta con la API de ingesta para responder consultas de operarios en campo.

## Endpoints de la API
- `POST /query` — para consultar documentos
- `GET /logs` — para ver historial de consultas

## Flujo del bot
1. Operario envía mensaje en lenguaje natural
2. Bot envía a `POST /query` → embedding → retrieval → MiniMax
3. Bot responde con texto + imagen si corresponde
4. Loguea cada consulta en `/logs`

## Configuración
- `TELEGRAM_BOT_TOKEN`: token del bot de @BotFather
- `API_URL`: URL de la API (ej: http://localhost:8000)

## Errores handling
- Si API no disponible → " временный код ошибки, попробуйте позже"
- Si respuesta vacía → "No encontré información relevante"

##部署
```bash
python -m src.bot.main
```

## Usage
El operario envía: "como se hace el revoque exterior?" → Bot responde con contexto del manual