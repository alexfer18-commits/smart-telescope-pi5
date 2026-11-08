# Security review

Scope: `pi5-software/`, `mobile-app/`, `firmware/`, `docker/`, `scripts/`.
Reviewed 2026-11-08. Revised 2026-11-08 after the ACL work.

**Status:** findings 1–5 are closed. Finding 5 is the one reported as critical #3
in the repository handover ("one MQTT credential for every client"); it is now
resolved by per-client identities and topic ACLs, verified against a running
broker.

**There is no firmware binary.** The Pi drives the A4988 carriers from Python
through gpiozero; the only compiled artifact in the tree is Python bytecode.
The Arduino sketch (`firmware/stepper_bridge.ino`) is source and was reviewed as
such, not as a binary — it was not compiled or flashed for this review.

The compiled-code pass used REA on `mqtt_bridge.pyc` (CPython 3.9, magic 3425,
4 213 bytes, SHA-256 `af3cc506…c921`). It confirmed the header, the code-object
graph, and the import set (`json`, `os`, `threading`, `time`, `typing`,
`paho.mqtt.client`), and found no credential material in the constant pool. REA
retains bytecode as length and hash only and does not decompile, so the source
review below is the substantive one.

## Fixed during this review

### 1. Retained MQTT command replays on every reconnect — high

`mqtt_bridge` subscribed to the command topic and executed whatever arrived. A
client that published with `retain=true` (one flag, no special access) would
have that command stored by the broker and re-delivered on every reconnect — a
slew command that fires unattended, hours later, at a mount nobody is watching.

Fixed in `_on_message`: retained messages are dropped before parsing. Commands
are never legitimately retained, so nothing is lost.

### 2. No soft limits: the mount could be driven into its own frame — high

`StepperAxis.move` accepts any angle. A 180° command at 6 °/s is 30 s of
full-speed motion into a hard stop, which strips the belt or stalls the driver
into thermal shutdown. Nothing in the driver prevents it, and an MQTT credential
is not a safety interlock.

Fixed in `MotorController`: altitude is clamped to `[-5°, 95°]` and azimuth to a
single rotation, with a `ValueError` rather than a silent clamp so the caller
learns it was refused. Covered by `test_altitude_soft_limit_is_enforced`.

### 3. MQTT password file world-readable — medium

`deploy.sh` created `docker/mosquitto/passwd` with the container's default
umask. Now `scripts/setup_mqtt_auth.sh` creates it with mode `600` and the ACL
file with `640`.

### 4. Token comparison was not constant-time — low

`dashboard.require_token` compared with `!=`. Now `hmac.compare_digest`. Over a
LAN the timing signal is not practically exploitable, but the fix is one line
and the pattern is the one that gets copied.

## Open, with recommendation

### 5. One MQTT credential for every client — high — **CLOSED**

Every client authenticated as `telescope` and could publish anywhere. The phone
held the same secret as the Pi, so a stolen phone was full control of the mount.

Now there are two identities with disjoint powers, enforced by
`docker/mosquitto/acl_file`:

| Identity | May read | May write |
|---|---|---|
| `pi` | `telescope/commands/#`, `telescope/pi/#` | `telescope/status/#`, `telescope/pi/#` |
| `phone` | `telescope/status/#` | `telescope/commands/#` |

Topics were renamed to match: the Pi publishes `telescope/status/state` and
rejections to `telescope/pi/rejected`; it reads commands from
`telescope/commands/cmd`. Everything else is denied by default.

Two ACL lines beyond the requested policy are required for the loop to function
at all — the phone must read what the Pi writes, and the Pi must read what the
phone writes. They are marked as such in `acl_file`; without them the broker is
secure and unusable.

The bridge now also refuses to construct without `MQTT_USER` and
`MQTT_PASSWORD`, so a missing environment variable fails closed instead of
silently producing an anonymous client.

Verified against a live broker, 9/9 passing
(`pi5-software/tests/test_mqtt_auth.py`):

- anonymous connect rejected; wrong password rejected;
- `pi` publishes state, `phone` receives it;
- `phone` commands, `pi` receives it;
- `pi` cannot forge a command;
- `phone` cannot spoof telemetry.

Residual: the broker container runs as its own user, so `passwd` must remain
readable to it. Mode `600` works with Docker Desktop's bind mounts; on a Linux
host where the container user differs from the file owner, use `640` with a
matching group rather than world-readable.

### 6. No audit trail of accepted commands — medium

Rejected commands are published to `telescope/pi/rejected`, but accepted ones are
not logged with the publishing client id. When a mount moves unexpectedly, the
first question is "who told it to".

*Recommendation:* log `(utc, client_id, cmd, args)` to a rotating file and to
InfluxDB. Ten lines in `mqtt_bridge`.

### 7. No watchdog for lost steps — medium

The serial protocol acknowledges every step, but nothing compares the
acknowledgement count against the commanded count at the end of a slew. A
dropped byte is a silently lost step, and the mount model absorbs it as
"pointing error" — which corrupts the experiment rather than failing it.

*Recommendation:* at the end of `StepperAxis.move`, compare `pulsed` against the
acknowledgements and raise if they differ by more than one step.

### 8. Self-signed certificate breaks the mobile client — medium (operational)

`tls_set()` uses the system CA store and the app sets
`rejectUnauthorized: true`. Both fail closed, which is correct, but the
consequence is that the phone cannot connect until the CA in
`docker/mosquitto/certs/ca.crt` is installed and trusted. `deploy.sh` prints
this, and it will still be the first support question.

*Recommendation:* ship a QR code in `docs/` that installs the CA profile, or pin
the certificate in the app. Do not relax `rejectUnauthorized`.

### 9. Plotly loaded from a CDN — low

The dashboard's HTML pulls `cdn.plot.ly`. That is third-party code executing in
the console of an instrument, and there is no CSP header.

*Recommendation:* vendor `plotly.min.js` into the dashboard image and add
`Content-Security-Policy: default-src 'self'`.

### 10. CLI scripts read arbitrary paths — low

`quantize_int8.py --calibration` and `check_equivalence.py --frames` accept any
directory. They are operator tools run by hand, not services, so this is not a
remote surface. No change recommended.

## What is already right, and should stay right

- No plaintext listener. 1883 is absent from `mosquitto.conf`, so there is no
  downgrade path.
- `allow_anonymous false` on both listeners.
- `dashboard.py` refuses to import without `TELESCOPE_API_TOKEN` — the failure
  mode is "does not start", not "starts open".
- `solve-field` is invoked with an argument list, never `shell=True`, and the
  hint is formatted as a float before it reaches argv.
- Command payloads are bounded at 512 bytes, axis names are whitelisted, and
  degrees are range-checked before any hardware call.
- No secret is hardcoded anywhere in the tree; `.env` is generated at deploy
  time with `openssl rand` and is git-ignored.
- Containers run as a non-root user (`telescope`, uid 10001).
