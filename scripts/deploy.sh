#!/usr/bin/env bash
# Deploy the telescope stack on a Raspberry Pi 5 (arm64).
# Idempotent: re-running regenerates nothing that already exists.
set -euo pipefail

cd "$(dirname "$0")/.."
CERT_DIR="docker/mosquitto/certs"
HOST_NAME="${TELESCOPE_HOST:-telescope.local}"

command -v docker >/dev/null || { echo "docker is required"; exit 1; }
docker compose version >/dev/null || { echo "docker compose v2 is required"; exit 1; }

# --- secrets -----------------------------------------------------------------
if [[ ! -f .env ]]; then
  umask 077
  cat > .env <<EOF
TELESCOPE_API_TOKEN=$(openssl rand -hex 24)
MQTT_PI_USER=pi
MQTT_PI_PASSWORD=$(openssl rand -hex 16)
MQTT_PHONE_USER=phone
MQTT_PHONE_PASSWORD=$(openssl rand -hex 16)
INFLUX_USER=telescope
INFLUX_PASSWORD=$(openssl rand -hex 16)
INFLUX_TOKEN=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -hex 16)
EOF
  echo "wrote .env (mode 600) — back it up, it is not in git"
fi
set -a; source .env; set +a

# --- TLS ---------------------------------------------------------------------
./scripts/gen_certs.sh

# --- MQTT identities and ACLs ------------------------------------------------
if [[ ! -f docker/mosquitto/passwd ]]; then
  MQTT_PI_PASSWORD="$MQTT_PI_PASSWORD" \
  MQTT_PHONE_PASSWORD="$MQTT_PHONE_PASSWORD" \
    ./scripts/setup_mqtt_auth.sh
fi

# --- run ---------------------------------------------------------------------
docker compose pull --quiet
docker compose up -d --build
docker compose ps
echo
echo "dashboard: https://$HOST_NAME:8443  (X-API-Key from .env)"
echo "grafana:   http://$HOST_NAME:3000"
