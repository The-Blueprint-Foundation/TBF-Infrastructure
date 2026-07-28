#!/usr/bin/env bash
###############################################################################
# scripts/tunnel.sh
#
# Opens SSH port-forwards through IAP TCP tunnels to give local access to all
# private resources in the VPC:
#
#   Local port 8000  →  fastapi-vm:8000     (FastAPI web server)
#   Local port 5432  →  SQL_IP:5432         (Cloud SQL PostgreSQL / pgAdmin)
#   Local port 1883  →  mqtt-vm:1883        (Mosquitto broker)
#
# FastAPI and PostgreSQL are forwarded via the FastAPI VM.
# MQTT is forwarded via the MQTT broker VM (separate IAP tunnel session).
# Both tunnel sessions are opened in the background and cleaned up on Ctrl-C.
#
# Usage:
#   bash scripts/tunnel.sh <PROJECT_ID> <ZONE> <API_VM> <MQTT_VM> <SQL_IP> <API_PORT>
#
# Or fill in DEFAULTS below and just run: bash scripts/tunnel.sh
#
# Requirements:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - IAP API enabled: gcloud services enable iap.googleapis.com
#   - Your Google account added to var.iap_tunnel_users in terraform.tfvars
###############################################################################

set -euo pipefail

# ── Arguments / defaults ──────────────────────────────────────────────────────
PROJECT_ID="${1:-YOUR_PROJECT_ID}"
ZONE="${2:-us-central1-a}"
API_VM="${3:-YOUR_API_VM_NAME}"
MQTT_VM="${4:-YOUR_MQTT_VM_NAME}"
SQL_IP="${5:-YOUR_SQL_PRIVATE_IP}"
API_PORT="${6:-8000}"

LOCAL_API_PORT="${API_PORT}"
LOCAL_PG_PORT="5432"
LOCAL_MQTT_PORT="1883"

# ── Validate gcloud is present ────────────────────────────────────────────────
if ! command -v gcloud &>/dev/null; then
  echo "ERROR: gcloud CLI not found. Install it from https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# ── Cleanup handler – kills both background tunnel sessions on exit ────────────
PIDS=()
cleanup() {
  echo ""
  echo "==> Closing tunnels..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  echo "    Done."
}
trap cleanup EXIT INT TERM

echo "==> Opening IAP tunnels"
echo "    FastAPI : http://localhost:${LOCAL_API_PORT}"
echo "    Postgres: localhost:${LOCAL_PG_PORT}  (connect pgAdmin here)"
echo "    MQTT    : localhost:${LOCAL_MQTT_PORT}  (broker / MQTT client)"
echo ""
echo "    Press Ctrl-C to close all tunnels."
echo ""

# ── Tunnel 1: FastAPI VM – forwards FastAPI port and PostgreSQL ───────────────
gcloud compute ssh "${API_VM}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --tunnel-through-iap \
  -- \
  -N \
  -L "${LOCAL_API_PORT}:localhost:${API_PORT}" \
  -L "${LOCAL_PG_PORT}:${SQL_IP}:5432" \
  -L "2222:localhost:22" &
PIDS+=($!)

# ── Tunnel 2: MQTT broker VM – forwards Mosquitto port ───────────────────────
gcloud compute ssh "${MQTT_VM}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --tunnel-through-iap \
  -- \
  -N \
  -L "${LOCAL_MQTT_PORT}:localhost:1883" \
  -L "2223:localhost:22" &
PIDS+=($!)

# Wait for both background jobs — script stays alive until Ctrl-C.
wait
