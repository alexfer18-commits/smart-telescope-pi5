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
MQTT_USER=telescope
MQTT_PASSWORD=$(openssl rand -hex 16)
INFLUX_USER=telescope
INFLUX_PASSWORD=$(openssl rand -hex 16)
INFLUX_TOKEN=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -hex 16)
EOF
  echo "wrote .env (mode 600) — back it up, it is not in git"
fi
set -a; source .env; set +a

# --- TLS ---------------------------------------------------------------------
if [[ ! -f "$CERT_DIR/server.crt" ]]; then
  mkdir -p "$CERT_DIR"
  openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
    -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \
    -subj "/CN=telescope-local-ca" 2>/dev/null
  openssl req -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
    -subj "/CN=$HOST_NAME" 2>/dev/null
  cat > "$CERT_DIR/server.ext" <<EOF
subjectAltName=DNS:$HOST_NAME,DNS:localhost,IP:127.0.0.1
EOF
  openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/server.crt" \
    -days 825 -sha256 -extfile "$CERT_DIR/server.ext" 2>/dev/null
  rm -f "$CERT_DIR/server.csr" "$CERT_DIR/server.ext"
  chmod 600 "$CERT_DIR"/*.key
  echo "generated CA and server certificate for $HOST_NAME"
  echo "install $CERT_DIR/ca.crt on the phone to trust the dashboard"
fi

# --- MQTT password file ------------------------------------------------------
if [[ ! -f docker/mosquitto/passwd ]]; then
  docker run --rm -v "$PWD/docker/mosquitto:/work" eclipse-mosquitto:2.0 \
    mosquitto_passwd -b -c /work/passwd "$MQTT_USER" "$MQTT_PASSWORD"
  chmod 640 docker/mosquitto/passwd
  echo "created docker/mosquitto/passwd"
fi

# --- run ---------------------------------------------------------------------
docker compose pull --quiet
docker compose up -d --build
docker compose ps
echo
echo "dashboard: https://$HOST_NAME:8443  (X-API-Key from .env)"
echo "grafana:   http://$HOST_NAME:3000"
