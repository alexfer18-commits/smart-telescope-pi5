#!/usr/bin/env bash
# Create the two MQTT identities (pi, phone) and tighten file permissions.
#
#   ./scripts/setup_mqtt_auth.sh
#
# Passwords come from MQTT_PI_PASSWORD / MQTT_PHONE_PASSWORD if set, otherwise
# they are generated and printed once. Re-running rotates the passwords, which
# disconnects every client until it is reconfigured — that is the point.
set -euo pipefail

cd "$(dirname "$0")/.."
MQTT_DIR="docker/mosquitto"
PASSWD="$MQTT_DIR/passwd"
ACL="$MQTT_DIR/acl_file"

[[ -f "$ACL" ]] || { echo "missing $ACL"; exit 1; }

PI_PASSWORD="${MQTT_PI_PASSWORD:-$(openssl rand -hex 16)}"
PHONE_PASSWORD="${MQTT_PHONE_PASSWORD:-$(openssl rand -hex 16)}"

umask 077
rm -f "$PASSWD"
docker run --rm -v "$PWD/$MQTT_DIR:/work" eclipse-mosquitto:2.0 \
  mosquitto_passwd -b -c /work/passwd pi "$PI_PASSWORD" >/dev/null
docker run --rm -v "$PWD/$MQTT_DIR:/work" eclipse-mosquitto:2.0 \
  mosquitto_passwd -b /work/passwd phone "$PHONE_PASSWORD" >/dev/null

# mosquitto_passwd hashes the values, so the file is not a plaintext store, but
# it is still a credential artifact: nobody else needs to read it.
chmod 600 "$PASSWD"
chmod 640 "$ACL"

cat <<EOF

MQTT identities created and ACL applied.

  pi     : $PI_PASSWORD
  phone  : $PHONE_PASSWORD

Store these in the Pi's .env (MQTT_PI_PASSWORD / MQTT_PHONE_PASSWORD) and in the
phone app's connection screen. The hash file is $PASSWD (mode 600).

If the broker runs as a non-root user inside the container it must be able to
read that file; see docs/security_report.md, finding #3.
EOF
