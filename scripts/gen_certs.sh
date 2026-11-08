#!/usr/bin/env bash
# Generate the local CA and the broker/dashboard server certificate.
# Idempotent: does nothing if the certificate already exists.
set -euo pipefail

cd "$(dirname "$0")/.."
CERT_DIR="docker/mosquitto/certs"
HOST_NAME="${TELESCOPE_HOST:-telescope.local}"

if [[ -f "$CERT_DIR/server.crt" ]]; then
  echo "certificate already present for $CERT_DIR/server.crt"
  exit 0
fi

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
