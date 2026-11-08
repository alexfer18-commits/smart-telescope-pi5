# Mobile console

React Native (Expo) client for the telescope. Three screens: connection,
live status with a calibrate action, and episode history.

## Why not VaneUI components

VaneUI is a web component library — 65 documentation pages, no React Native
target (`vaneui search_docs "react native"` returns nothing). Its components
cannot be imported into a native app, so `src/theme.ts` transcribes its prop
vocabulary (`appearance`, `variant`, `size`, `shape`, `rounded|pill|sharp`)
into concrete tokens. A web dashboard built with VaneUI itself would use the
real components and the same tokens; that is the natural next step if a browser
console is wanted.

## Run

```bash
cd mobile-app
npm install
npx expo start          # scan the QR with Expo Go on the phone
npm run typecheck
```

The Pi must expose MQTT over WebSocket (`listener 9001` + `protocol websockets`
in `docker/mosquitto/mosquitto.conf`) and the dashboard on 8443 with the same
certificate. Both are TLS-only; `rejectUnauthorized: true` is deliberate and
should not be relaxed for convenience.

## What is deliberately missing

No state persistence, no offline queue, no push notifications. The console is a
remote control for a device on the same network, and every one of those features
would need a decision about credentials on the phone.
