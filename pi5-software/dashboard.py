"""FastAPI dashboard: status, calibration trigger, and session history.

Run on the Pi:  uvicorn dashboard:app --host 0.0.0.0 --port 8000

Auth is a single shared token in ``TELESCOPE_API_TOKEN``. Without it the app
refuses to start, so an instrument is never exposed unauthenticated by
accident. The HTML view is read-only; commands go through POST endpoints.
"""

from __future__ import annotations

import hmac
import os
import time
from collections import deque
from dataclasses import asdict, dataclass, field

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

API_TOKEN = os.environ.get("TELESCOPE_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("TELESCOPE_API_TOKEN must be set; refusing to start open")

app = FastAPI(title="Smart Telescope Pi 5", version="0.1.0")


@dataclass
class TelescopeState:
    ra_deg: float = 0.0
    dec_deg: float = 0.0
    error_arcmin: float = 0.0
    latency_ms: float = 0.0
    n_stars: int = 0
    pointing: bool = False
    last_solve_utc: float = 0.0
    history: deque = field(default_factory=lambda: deque(maxlen=120))


STATE = TelescopeState()


def require_token(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key is None or not hmac.compare_digest(x_api_key, API_TOKEN):
        raise HTTPException(status_code=401, detail="invalid API key")


def _status_payload() -> dict:
    data = asdict(STATE)
    data.pop("history", None)
    data["uptime_s"] = round(time.monotonic(), 1)
    return data


@app.get("/status")
def status(_: None = Depends(require_token)) -> dict:
    return _status_payload()


@app.get("/history")
def history(_: None = Depends(require_token)) -> dict:
    return {"episodes": list(STATE.history)}


@app.post("/calibrate")
def calibrate(_: None = Depends(require_token)) -> dict:
    """Request a calibration run. The control loop picks this up on its next tick."""
    STATE.pointing = True
    return {"accepted": True, "requested_utc": time.time()}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Plotly view of the last 120 solves. Token is supplied by the browser."""
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>Telescope</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script></head>
<body style="font-family:system-ui;margin:2rem">
<h2>Pointing error, last 120 solves</h2>
<div id="plot" style="height:420px"></div>
<script>
const token = prompt("API token") || "";
async function refresh() {
  const r = await fetch("/history", {headers: {"X-API-Key": token}});
  const {episodes} = await r.json();
  Plotly.newPlot("plot", [{
    x: episodes.map(e => new Date(e.t * 1000)),
    y: episodes.map(e => e.error_arcmin),
    mode: "lines+markers", name: "arcmin"
  }], {yaxis: {title: "arcmin"}, margin: {t: 20}});
}
refresh(); setInterval(refresh, 5000);
</script></body></html>"""
