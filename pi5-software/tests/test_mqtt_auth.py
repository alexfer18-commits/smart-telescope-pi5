"""MQTT authentication and ACL tests.

Two tiers:

* Always run: the bridge refuses to build without credentials (fail-closed).
* ``MQTT_TEST_HOST`` set: talk to a real broker started from docker-compose and
  verify that anonymous clients are rejected and that the ACLs actually deny the
  topics they are supposed to deny. Skipping is explicit, never silent.

    docker compose up -d mosquitto
    MQTT_TEST_HOST=localhost \
    MQTT_TEST_CA=docker/mosquitto/certs/ca.crt \
    MQTT_TEST_PI_PASSWORD=... MQTT_TEST_PHONE_PASSWORD=... \
    pytest pi5-software/tests/test_mqtt_auth.py -v
"""

from __future__ import annotations

import os
import time
import uuid

import pytest

from mqtt_bridge import CommandRejected, MqttBridge, parse_command


# --- always-run unit tests ---------------------------------------------------

def test_bridge_refuses_to_build_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("MQTT_USER", raising=False)
    monkeypatch.delenv("MQTT_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="MQTT_USER and MQTT_PASSWORD"):
        MqttBridge(lambda: {}, lambda cmd: None, host="127.0.0.1")


def test_bridge_refuses_half_credentials(monkeypatch) -> None:
    monkeypatch.setenv("MQTT_USER", "pi")
    monkeypatch.delenv("MQTT_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        MqttBridge(lambda: {}, lambda cmd: None, host="127.0.0.1")


def test_command_validation_still_rejects_junk() -> None:
    for payload in (b"", b"{}", b'{"cmd":"move","axis":"az"}',
                    b'{"cmd":"move","axis":"az","deg":1e9}'):
        with pytest.raises(CommandRejected):
            parse_command(payload)


# --- broker integration tests ------------------------------------------------

HOST = os.environ.get("MQTT_TEST_HOST")
CA = os.environ.get("MQTT_TEST_CA", "docker/mosquitto/certs/ca.crt")
PORT = int(os.environ.get("MQTT_TEST_PORT", "8883"))
PI = (os.environ.get("MQTT_TEST_PI_USER", "pi"),
      os.environ.get("MQTT_TEST_PI_PASSWORD", ""))
PHONE = (os.environ.get("MQTT_TEST_PHONE_USER", "phone"),
         os.environ.get("MQTT_TEST_PHONE_PASSWORD", ""))

broker = pytest.mark.skipif(
    not HOST, reason="set MQTT_TEST_HOST to run broker ACL tests")


def _client(credentials: tuple[str, str] | None) -> "object":
    import paho.mqtt.client as mqtt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"test-{uuid.uuid4().hex[:8]}")
    if credentials is not None:
        client.username_pw_set(*credentials)
    client.tls_set(ca_certs=CA)
    return client


def _connect(client, timeout: float = 8.0):
    seen: dict[str, object] = {}

    def on_connect(_c, _u, _flags, reason_code, _props) -> None:
        seen["rc"] = reason_code

    client.on_connect = on_connect
    client.connect(HOST, PORT, keepalive=30)
    client.loop_start()
    deadline = time.time() + timeout
    while "rc" not in seen and time.time() < deadline:
        time.sleep(0.02)
    if "rc" not in seen:
        client.loop_stop()
        pytest.fail("broker did not send CONNACK")
    return seen["rc"]


def _wait_for(predicate, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


@broker
def test_anonymous_client_is_rejected() -> None:
    client = _client(None)
    reason = _connect(client)
    client.loop_stop()
    client.disconnect()
    assert reason.is_failure, f"anonymous connect unexpectedly allowed: {reason}"


@broker
def test_wrong_password_is_rejected() -> None:
    client = _client((PI[0], "definitely-not-the-password"))
    reason = _connect(client)
    client.loop_stop()
    client.disconnect()
    assert reason.is_failure


@broker
def test_pi_can_publish_state_and_phone_reads_it() -> None:
    received: list[bytes] = []
    sub = _client(PHONE)
    sub.on_message = lambda _c, _u, msg: received.append(msg.payload)
    assert not _connect(sub).is_failure
    sub.subscribe("telescope/status/#", qos=1)
    time.sleep(0.3)

    pub = _client(PI)
    assert not _connect(pub).is_failure
    pub.publish("telescope/status/state", b'{"ra_deg":210.0}', qos=1)

    assert _wait_for(lambda: len(received) > 0), "phone did not receive state"
    for c in (sub, pub):
        c.loop_stop()
        c.disconnect()


@broker
def test_pi_cannot_publish_commands() -> None:
    """The Pi must not be able to forge a command to itself or to the network."""
    received: list[bytes] = []
    sub = _client(PI)
    sub.on_message = lambda _c, _u, msg: received.append(msg.payload)
    assert not _connect(sub).is_failure
    sub.subscribe("telescope/commands/#", qos=1)
    time.sleep(0.3)

    sub.publish("telescope/commands/cmd", b'{"cmd":"stop"}', qos=1)
    time.sleep(1.0)
    sub.loop_stop()
    sub.disconnect()
    assert received == [], f"ACL let the Pi publish a command: {received}"


@broker
def test_phone_can_command_and_pi_receives_it() -> None:
    received: list[bytes] = []
    sub = _client(PI)
    sub.on_message = lambda _c, _u, msg: received.append(msg.payload)
    assert not _connect(sub).is_failure
    sub.subscribe("telescope/commands/#", qos=1)
    time.sleep(0.3)

    phone = _client(PHONE)
    assert not _connect(phone).is_failure
    phone.publish("telescope/commands/cmd", b'{"cmd":"stop"}', qos=1)

    assert _wait_for(lambda: len(received) > 0), "Pi did not receive the command"
    for c in (sub, phone):
        c.loop_stop()
        c.disconnect()


@broker
def test_phone_cannot_publish_state() -> None:
    """A phone must not be able to spoof the telescope's own telemetry."""
    received: list[bytes] = []
    sub = _client(PHONE)
    sub.on_message = lambda _c, _u, msg: received.append(msg.payload)
    assert not _connect(sub).is_failure
    sub.subscribe("telescope/status/#", qos=1)
    time.sleep(0.3)

    sub.publish("telescope/status/state", b'{"spoofed":true}', qos=1)
    time.sleep(1.0)
    forged = [m for m in received if b"spoofed" in m]
    sub.loop_stop()
    sub.disconnect()
    assert forged == [], "ACL let the phone publish state"
