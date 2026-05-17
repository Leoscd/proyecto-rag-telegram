# TAREA 014 — Deploy en VPS: systemd + Tailscale + instrucciones

- Fecha asignada: 2026-05-17
- Fase del MVP: 4 — Pulido demo
- Estimación: ≤ 1 día
- Depende de: TAREA 013 (MVP funcional completo)

## Objetivo
Dejar el MVP corriendo de forma estable en el VPS (2GB/1vCPU, red privada Tailscale) con dos servicios systemd: la API y el bot. Que arranquen solos al reiniciar el VPS y que los logs sean accesibles con journalctl.

## Contexto del VPS

- OS: Linux (Ubuntu/Debian)
- RAM: 2GB / 1vCPU — compartido con el agente MiniMax del colaborador
- Red: Tailscale (IP privada `100.x.x.x`) — NO exponer a Internet público
- El bot usa long polling — no necesita puerto público
- La API escucha solo en la IP de Tailscale (no en 0.0.0.0)

## Archivos a crear

- `deploy/rag-api.service` — unit systemd para la API
- `deploy/rag-bot.service` — unit systemd para el bot
- `deploy/setup.sh` — script de instalación en el VPS (idempotente)
- `deploy/README.md` — instrucciones de deploy paso a paso

## Contrato

### deploy/rag-api.service

```ini
[Unit]
Description=RAG-Obras API
After=network.target

[Service]
Type=simple
User=ragobras
WorkingDirectory=/srv/rag-obras
EnvironmentFile=/srv/rag-obras/.env
ExecStart=/srv/rag-obras/.venv/bin/uvicorn src.api.main:app \
          --host 0.0.0.0 --port 8000 --workers 1
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**IMPORTANTE:** `--workers 1` — 1 vCPU, no más. `--host 0.0.0.0` porque Tailscale filtra a nivel de red, no hace falta bind a IP específica para el MVP.

### deploy/rag-bot.service

```ini
[Unit]
Description=RAG-Obras Bot Telegram
After=network.target rag-api.service

[Service]
Type=simple
User=ragobras
WorkingDirectory=/srv/rag-obras
EnvironmentFile=/srv/rag-obras/.env
ExecStart=/srv/rag-obras/.venv/bin/python -m src.bot.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### deploy/setup.sh

Script que ejecuta el jefe de obra (o Leonardo) la primera vez en el VPS:

```bash
#!/bin/bash
set -e

DEPLOY_DIR="/srv/rag-obras"
SERVICE_USER="ragobras"
REPO_URL="https://github.com/Leoscd/proyecto-rag-telegram.git"

echo "=== Setup RAG-Obras ==="

# 1. Crear usuario si no existe
id -u $SERVICE_USER &>/dev/null || useradd -r -s /bin/false $SERVICE_USER

# 2. Clonar o actualizar repo
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "Actualizando repo..."
    cd $DEPLOY_DIR && git pull
else
    echo "Clonando repo..."
    git clone $REPO_URL $DEPLOY_DIR
fi

# 3. Crear venv e instalar dependencias
cd $DEPLOY_DIR
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 4. Verificar .env
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo "⚠️  FALTA: copiar .env.example a .env y completar las keys"
    echo "    cp $DEPLOY_DIR/.env.example $DEPLOY_DIR/.env"
    echo "    nano $DEPLOY_DIR/.env"
    exit 1
fi

# 5. Instalar services
cp deploy/rag-api.service /etc/systemd/system/
cp deploy/rag-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable rag-api rag-bot
systemctl restart rag-api rag-bot

# 6. Permisos
chown -R $SERVICE_USER:$SERVICE_USER $DEPLOY_DIR

echo ""
echo "=== Estado de los servicios ==="
systemctl status rag-api --no-pager
systemctl status rag-bot --no-pager
echo ""
echo "=== Ver logs ==="
echo "journalctl -u rag-api -f"
echo "journalctl -u rag-bot -f"
echo ""
echo "=== Health check ==="
echo "curl http://localhost:8000/"
```

### deploy/README.md

Instrucciones humanas paso a paso:

```markdown
# Deploy RAG-Obras en VPS

## Prerequisitos
- VPS Ubuntu/Debian con Python 3.11+, git, Tailscale activo
- Puerto 8000 accesible dentro de la Tailnet (no público)

## Primera vez
1. SSH al VPS: `ssh user@100.x.x.x`
2. `sudo bash deploy/setup.sh`
3. Completar `/srv/rag-obras/.env` con las API keys reales
4. `sudo systemctl restart rag-api rag-bot`

## Actualizar código
1. `cd /srv/rag-obras && git pull`
2. `.venv/bin/pip install -r requirements.txt`
3. `sudo systemctl restart rag-api rag-bot`

## Verificar estado
- `systemctl status rag-api rag-bot`
- `journalctl -u rag-api -f` (logs en tiempo real)
- `curl http://localhost:8000/` desde el VPS

## Monitoreo de recursos
- `free -m` → verificar RAM disponible (mínimo 500MB libre)
- `top` → verificar que uvicorn/python no superen 50% de CPU en reposo

## Solución de problemas
- **API no arranca:** `journalctl -u rag-api -n 50` → buscar error de import o de .env
- **Bot no arranca:** verificar TELEGRAM_BOT_TOKEN en .env, `journalctl -u rag-bot -n 50`
- **OOM (out of memory):** reducir `--workers 1` ya está; verificar que no haya otro proceso pesado
```

## Criterios de aceptación
- [ ] `deploy/rag-api.service` y `deploy/rag-bot.service` son válidos (revisar sintaxis)
- [ ] `deploy/setup.sh` es ejecutable y tiene `set -e`
- [ ] Los services usan `EnvironmentFile` (no hardcodean secrets)
- [ ] `--workers 1` en uvicorn (restricción VPS)
- [ ] `deploy/README.md` tiene instrucciones claras para actualizar código post-deploy
- [ ] El colaborador NO necesita ejecutar esto en el VPS real — solo commitear los archivos

## Nota importante
Esta tarea crea los archivos de deploy, pero **la ejecución en el VPS la hace Leonardo**. El colaborador entrega los archivos correctos; no tiene acceso al VPS de producción.

## Qué NO hacer
- Sin nginx, sin reverse proxy — la API es accesible directo dentro de la Tailnet
- Sin docker — demasiado overhead para 2GB de RAM
- Sin webhook de Telegram — long polling siempre
- No exponer el puerto 8000 a Internet público

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_014_resumen.md`:

```markdown
# Resumen TAREA 014

## Archivos creados
## Decisiones tomadas (ej: por qué 1 worker, por qué no nginx)
## Problemas o dudas sobre el VPS
## Cómo validar los service files sin VPS real (ej: systemd-analyze verify)
```
