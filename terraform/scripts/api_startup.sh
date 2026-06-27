#!/usr/bin/env bash
###############################################################################
# env_startup.sh – runs once on first boot via instance metadata.
# Installs Python, creates a systemd service for FastAPI/uvicorn.
#
# Template variables injected by Terraform templatefile():
#   api_port – port uvicorn will bind to
###############################################################################

set -euo pipefail
exec > >(tee /var/log/startup.log | logger -t startup-script) 2>&1

echo "==> Starting startup script"

# ── Read DB connection info from instance metadata ────────────────────────────
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
HEADER="Metadata-Flavor: Google"

DB_HOST=$(curl -sf -H "$HEADER" "$METADATA_URL/db-host")
DB_NAME=$(curl -sf -H "$HEADER" "$METADATA_URL/db-name")
DB_USER=$(curl -sf -H "$HEADER" "$METADATA_URL/db-user")
DB_PASS=$(curl -sf -H "$HEADER" "$METADATA_URL/db-password")

DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST/$DB_NAME"

# ── System packages ───────────────────────────────────────────────────────────
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git

# ── Application directory ─────────────────────────────────────────────────────
APP_DIR="/opt/fastapi-app"
mkdir -p "$${APP_DIR}"

# ── Python virtual environment ────────────────────────────────────────────────
python3 -m venv "$${APP_DIR}/.venv"
"$${APP_DIR}/.venv/bin/pip" install --quiet --upgrade pip
"$${APP_DIR}/.venv/bin/pip" install --quiet fastapi uvicorn[standard] asyncpg sqlalchemy psycopg2-binary

# ── Example application (replace with your real app or a git clone) ───────────
cat > "$${APP_DIR}/main.py" << 'PYTHON'
from fastapi import FastAPI

app = FastAPI(title="FastAPI on GCP")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello from FastAPI on Google Cloud!"}
PYTHON

# ── Environment file (keeps credentials out of the process table) ─────────────
cat > "$${APP_DIR}/.env" << ENV
DATABASE_URL=$${DATABASE_URL}
ENV
chmod 600 "$${APP_DIR}/.env"

# ── systemd service ───────────────────────────────────────────────────────────
cat > /etc/systemd/system/fastapi.service << SERVICE
[Unit]
Description=FastAPI application
After=network.target

[Service]
User=nobody
WorkingDirectory=$${APP_DIR}
EnvironmentFile=$${APP_DIR}/.env
ExecStart=$${APP_DIR}/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${api_port} --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable fastapi
systemctl start fastapi

echo "==> Startup script complete. FastAPI listening on port ${api_port}."
