#!/usr/bin/env bash
###############################################################################
# scripts/mqtt_startup.sh – runs once on first boot.
# Installs Mosquitto and Python dependencies for the subscriber you'll write.
#
# Template variables injected by Terraform templatefile():
#   mqtt_port – port Mosquitto will listen on (default 1883)
###############################################################################

set -euo pipefail
exec > >(tee /var/log/startup.log | logger -t startup-script) 2>&1

echo "==> Starting MQTT broker startup script"

# ── System packages ───────────────────────────────────────────────────────────
apt-get update -qq
apt-get install -y -qq mosquitto mosquitto-clients python3 python3-pip python3-venv

# ── Mosquitto configuration ───────────────────────────────────────────────────
# Anonymous access, listening on the configured port, local persistence.
cat > /etc/mosquitto/conf.d/broker.conf << CONF
listener ${mqtt_port}
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
CONF

systemctl enable mosquitto
systemctl restart mosquitto

# ── Python environment for your subscriber process ────────────────────────────
# Dependencies are pre-installed so you can start writing without any setup.
SUBSCRIBER_DIR="/opt/mqtt-subscriber"
mkdir -p "$SUBSCRIBER_DIR"

python3 -m venv "$SUBSCRIBER_DIR/.venv"
"$SUBSCRIBER_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SUBSCRIBER_DIR/.venv/bin/pip" install --quiet \
  paho-mqtt \
  psycopg2-binary \
  python-dotenv

# ── Write a .env stub for the subscriber to read ─────────────────────────────
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
HEADER="Metadata-Flavor: Google"

DB_HOST=$(curl -sf -H "$HEADER" "$METADATA_URL/db-host")
DB_NAME=$(curl -sf -H "$HEADER" "$METADATA_URL/db-name")
DB_USER=$(curl -sf -H "$HEADER" "$METADATA_URL/db-user")
DB_PASS=$(curl -sf -H "$HEADER" "$METADATA_URL/db-password")

cat > "$SUBSCRIBER_DIR/.env" << ENV
MQTT_HOST=localhost
MQTT_PORT=${mqtt_port}
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST/$DB_NAME
ENV
chmod 600 "$SUBSCRIBER_DIR/.env"

# ── Placeholder for your subscriber script ────────────────────────────────────
# Drop your subscriber.py here and activate the venv to run it:
#   source /opt/mqtt-subscriber/.venv/bin/activate
#   python subscriber.py
#
# When ready to run it as a service, create a systemd unit at:
#   /etc/systemd/system/mqtt-subscriber.service
# A minimal template:
#
# [Unit]
# Description=MQTT subscriber
# After=network.target mosquitto.service
#
# [Service]
# User=nobody
# WorkingDirectory=/opt/mqtt-subscriber
# EnvironmentFile=/opt/mqtt-subscriber/.env
# ExecStart=/opt/mqtt-subscriber/.venv/bin/python subscriber.py
# Restart=always
# RestartSec=5
#
# [Install]
# WantedBy=multi-user.target

echo "==> MQTT broker startup complete. Mosquitto listening on port ${mqtt_port}."
echo "    Subscriber venv ready at /opt/mqtt-subscriber/.venv"
echo "    Connection details written to /opt/mqtt-subscriber/.env"
