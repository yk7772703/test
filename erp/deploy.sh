#!/bin/bash
# ComplianceERP Deployment Script
# Usage: ./deploy.sh [domain.com]
# After running, configure your DNS A record to point to this server's IP.

set -e

DOMAIN=${1:-"localhost"}
BACKEND_PORT=8000
FRONTEND_DIR="/home/user/test/erp/frontend"
BACKEND_DIR="/home/user/test/erp/backend"

echo "=== ComplianceERP Deploy ==="
echo "Domain: $DOMAIN"

# 1. Build frontend with correct API URL
cd "$FRONTEND_DIR"
VITE_API_URL="https://$DOMAIN" npm run build

# 2. Install/update backend deps
cd "$BACKEND_DIR"
pip install -r requirements.txt -q

# 3. Ensure .env exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env — please set SECRET_KEY to a strong random value!"
fi

# 4. Create DB tables and seed
python -c "
import app.models
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print('DB tables OK')
"

# 5. Start/restart backend (using systemd or simple nohup)
pkill -f "uvicorn app.main" 2>/dev/null || true
sleep 1
nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT \
  --workers 4 --log-level info > /var/log/erp_backend.log 2>&1 &
echo "Backend started on port $BACKEND_PORT (PID: $!)"

# 6. Print nginx config suggestion
echo ""
echo "=== Nginx config (copy to /etc/nginx/sites-enabled/erp) ==="
cat << NGINX
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL — use certbot: certbot --nginx -d $DOMAIN
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location /api {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
NGINX
echo ""
echo "=== After nginx setup, run: ==="
echo "  certbot --nginx -d $DOMAIN"
echo ""
echo "=== App is live at: http://$DOMAIN ==="
echo "=== Login: admin@erp.com / Admin123! (change password after first login!) ==="
