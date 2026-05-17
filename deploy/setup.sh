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
systemctl enable rag-api rag-bot || true
systemctl restart rag-api rag-bot || true

# 6. Permisos
chown -R $SERVICE_USER:$SERVICE_USER $DEPLOY_DIR

echo ""
echo "=== Estado de los servicios ==="
systemctl status rag-api --no-pager || true
systemctl status rag-bot --no-pager || true
echo ""
echo "=== Ver logs ==="
echo "journalctl -u rag-api -f"
echo "journalctl -u rag-bot -f"
echo ""
echo "=== Health check ==="
echo "curl http://localhost:8000/"