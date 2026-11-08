"""MQTT bridge: publishes telescope state, accepts validated commands.

Topics (matching docker/mosquitto/acl_file)
------------------------------------------
``telescope/status/state``    JSON, published every second (retained).
``telescope/commands/cmd``    JSON commands: {"cmd": "move", "axis": "az", "deg": 1.5}
                              {"cmd": "stop"} | {"cmd": "calibrate"}
``telescope/pi/rejected``     JSON, why a command was refused.

The bridge never trusts a command: axis is whitelisted, degrees are bounded,
and payloads over 512 bytes are dropped. Credentials are mandatory — a bridge
with no identity is refused at construction, because a broker that accepts
anonymous clients is one bad config edit away from accepting anonymous slews.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Callable

import paho.mqtt.client as mqtt

STATE_TOPIC = "telescope/status/state"
CMD_TOPIC = "telescope/commands/cmd"
REJECT_TOPIC = "telescope/pi/rejected"
MAX_PAYLOAD = 512
MAX_SLEW_DEG = 180.0
VALID_AXES = {"az", "alt"}


class CommandRejected(ValueError):
    pass


def parse_command(payload: bytes) -> dict:
    """Validate a command payload. Raises CommandRejected on anything odd."""
    if len(payload) > MAX_PAYLOAD:
        raise CommandRejected("payload too large")
    try:
        cmd = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CommandRejected("not JSON") from exc
    if not isinstance(cmd, dict) or cmd.get("cmd") not in {"move", "stop", "calibrate"}:
        raise CommandRejected("unknown command")
    if cmd["cmd"] == "move":
        if cmd.get("axis") not in VALID_AXES:
            raise CommandRejected("unknown axis")
        deg = cmd.get("deg")
        if not isinstance(deg, (int, float)) or abs(deg) > MAX_SLEW_DEG:
            raise CommandRejected("degrees out of range")
    return cmd


class MqttBridge:
    def __init__(self, state_provider: Callable[[], dict],
                 command_handler: Callable[[dict], None],
                 host: str | None = None, port: int | None = None,
                 tls: bool = True, period_s: float = 1.0) -> None:
        self._state = state_provider
        self._handle = command_handler
        self._period = period_s
        self._stop = threading.Event()

        user = os.environ.get("MQTT_USER")
        password = os.environ.get("MQTT_PASSWORD")
        if not user or not password:
            raise RuntimeError(
                "MQTT_USER and MQTT_PASSWORD are required; refusing to build an "
                "unauthenticated control client")

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id="telescope-pi5")
        if tls:
            self._client.tls_set()          # system CA store; broker cert must match host
        self._client.username_pw_set(user, password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect(host or os.environ.get("MQTT_HOST", "localhost"),
                             port or int(os.environ.get("MQTT_PORT", "8883")))
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _loop(self) -> None:
        self._client.loop_start()
        while not self._stop.is_set():
            try:
                self._client.publish(STATE_TOPIC, json.dumps(self._state()), qos=1,
                                     retain=True)
            except Exception as exc:  # never let telemetry kill the control loop
                print(f"mqtt publish failed: {exc}")
            self._stop.wait(self._period)
        self._client.loop_stop()

    def _on_connect(self, client: mqtt.Client, userdata, flags, reason_code, props) -> None:
        client.subscribe(CMD_TOPIC, qos=1)

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        if msg.retain:
            # A retained command would replay on every reconnect and slew the
            # mount unattended. Commands are never retained; drop them.
            return
        try:
            self._handle(parse_command(msg.payload))
        except CommandRejected as exc:
            client.publish(REJECT_TOPIC, json.dumps({"reason": str(exc)}), qos=1)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._client.disconnect()
