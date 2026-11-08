/**
 * Transport to the telescope: MQTT over WebSocket for live state, HTTPS for
 * commands. Both require credentials; nothing is anonymous.
 *
 * The Pi runs mosquitto with a TLS listener on 8883 (MQTT) and the dashboard
 * behind the same certificate on 8443. For the WebSocket listener add a
 * `listener 9001` + `protocol websockets` block to mosquitto.conf.
 */

import mqtt, { MqttClient } from "mqtt";

export interface TelescopeState {
  ra_deg: number;
  dec_deg: number;
  error_arcmin: number;
  latency_ms: number;
  n_stars: number;
  pointing: boolean;
  last_solve_utc: number;
}

export interface Episode {
  t: number;
  error_arcmin: number;
  latency_ms: number;
}

export class TelescopeClient {
  private client: MqttClient | null = null;

  constructor(
    private readonly host: string,
    private readonly token: string,
    private readonly user = "telescope",
    private readonly password = "",
  ) {}

  connect(onState: (s: TelescopeState) => void,
          onError: (message: string) => void): void {
    const url = `wss://${this.host}:9001/mqtt`;
    this.client = mqtt.connect(url, {
      username: this.user,
      password: this.password,
      rejectUnauthorized: true,
      reconnectPeriod: 3000,
    });
    this.client.on("connect", () => this.client?.subscribe("telescope/state"));
    this.client.on("message", (_topic, payload) => {
      try {
        onState(JSON.parse(payload.toString()) as TelescopeState);
      } catch {
        onError("malformed state payload");
      }
    });
    this.client.on("error", (err) => onError(err.message));
  }

  async calibrate(): Promise<void> {
    await this.post("/calibrate");
  }

  async history(): Promise<Episode[]> {
    const response = await fetch(`https://${this.host}:8443/history`, {
      headers: { "X-API-Key": this.token },
    });
    if (!response.ok) throw new Error(`history failed: ${response.status}`);
    return ((await response.json()) as { episodes: Episode[] }).episodes;
  }

  private async post(path: string): Promise<void> {
    const response = await fetch(`https://${this.host}:8443${path}`, {
      method: "POST",
      headers: { "X-API-Key": this.token },
    });
    if (!response.ok) throw new Error(`${path} failed: ${response.status}`);
  }

  disconnect(): void {
    this.client?.end(true);
    this.client = null;
  }
}
