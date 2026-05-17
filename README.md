# proyecto-rag-telegram

Sistema de inteligencia operativa para obras de construcción: el admin carga documentos desde un panel web, el operario consulta por Telegram en lenguaje natural, y un dashboard controla la calidad de las respuestas RAG.

- **Fuente de verdad del producto:** [`BRIEFING_CLAUDE_CODE.md`](BRIEFING_CLAUDE_CODE.md)
- **Reglas de ejecución (colaborador / MiniMax 2.7):** [`CLAUDE.md`](CLAUDE.md)
- **Tareas diarias:** carpeta [`tareas/`](tareas/) — hacer **solo** la tarea del día, contra sus criterios de aceptación.

## Stack

FastAPI · python-telegram-bot · OpenAI `text-embedding-3-large` (3072) · MiniMax API · Supabase (pgvector/Storage/Postgres) · front HTML/CSS/JS vanilla. Deploy en VPS Linux (2GB/1vCPU) con systemd, red privada Tailscale. Sin modelos locales pesados.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # completar las claves
```

Variables requeridas en `.env`: `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`.
