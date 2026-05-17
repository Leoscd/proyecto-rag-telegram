# Deploy RAG-Obras en VPS

## Prerequisitos
- VPS Ubuntu/Debian con Python 3.11+, git
- Tailscale activo (red privada)
- Puerto 8000 accesible dentro de la Tailnet (NO expuesto a Internet público)

## Estructura del VPS
- **RAM**: 2GB / 1vCPU — compartido
- **Red**: Tailscale (`100.x.x.x`) — solo acceso interno
- **Usuario**: `ragobras` (se crea automáticamente)

## Primera vez (setup.sh)

```bash
# SSH al VPS
ssh user@100.x.x.x

# Ejecutar setup
sudo bash deploy/setup.sh

# Completar .env con las API keys reales
nano /srv/rag-obras/.env

# Reiniciar servicios
sudo systemctl restart rag-api rag-bot
```

## Actualizar código post-deploy

```bash
cd /srv/rag-obras
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart rag-api rag-bot
```

## Verificar estado

```bash
# Estado de servicios
systemctl status rag-api rag-bot

# Logs en tiempo real
journalctl -u rag-api -f
journalctl -u rag-bot -f

# Health check
curl http://localhost:8000/
```

## Monitoreo de recursos

```bash
# RAM libre (mínimo 500MB libres)
free -m

# CPU
top
```

## Solución de problemas

| Problema | Solución |
|---------|---------|
| API no arranca | `journalctl -u rag-api -n 50` |
| Bot no arranca | Verificar `TELEGRAM_BOT_TOKEN` en .env |
| OOM | Ya hay `--workers 1`; verificar procesos |

## Puertos y acceso

- **API**: `http://100.x.x.x:8000` (solo red Tailscale)
- **Admin**: `http://100.x.x.x:8000/admin`
- **Dashboard**: `http://100.x.x.x:8000/dashboard`
- **Bot**: long polling (no necesita puerto público)

## Archivos de deploy

- `deploy/rag-api.service` — systemd para API
- `deploy/rag-bot.service` — systemd para Bot
- `deploy/setup.sh` — script de instalación