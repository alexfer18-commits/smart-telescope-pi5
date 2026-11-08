/**
 * Smart Telescope — mobile console.
 *
 * Three screens, no navigation dependency: a tab state machine is enough for
 * four views and keeps the skeleton readable.
 *
 *   1. Connect  — broker host, MQTT user/password, dashboard API token
 *   2. Status   — live RA/Dec, pointing error, latency, calibrate button
 *   3. History  — last N episodes as a bar list, no chart library needed
 *
 * Theming follows VaneUI's prop vocabulary (appearance/variant/size/shape);
 * see src/theme.ts for why the components themselves are not imported.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator, Pressable, SafeAreaView, ScrollView, StyleSheet,
  Text, TextInput, View,
} from "react-native";

import { Episode, TelescopeClient, TelescopeState } from "./src/telescopeClient";
import { appearanceColor, Appearance, colors, fontSize, radius, space } from "./src/theme";

type Tab = "connect" | "status" | "history";

const EMPTY_STATE: TelescopeState = {
  ra_deg: 0, dec_deg: 0, error_arcmin: 0, latency_ms: 0,
  n_stars: 0, pointing: false, last_solve_utc: 0,
};

export default function App() {
  const [tab, setTab] = useState<Tab>("connect");
  const [host, setHost] = useState("telescope.local");
  const [user, setUser] = useState("telescope");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [state, setState] = useState<TelescopeState>(EMPTY_STATE);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const client = useMemo(
    () => (token ? new TelescopeClient(host, token, user, password) : null),
    [host, token, user, password],
  );

  useEffect(() => () => client?.disconnect(), [client]);

  const connect = useCallback(() => {
    if (!client) {
      setError("API token is required");
      return;
    }
    setError(null);
    client.connect(setState, setError);
    setTab("status");
  }, [client]);

  const calibrate = useCallback(async () => {
    if (!client) return;
    setBusy(true);
    try {
      await client.calibrate();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }, [client]);

  const loadHistory = useCallback(async () => {
    if (!client) return;
    setBusy(true);
    try {
      setEpisodes(await client.history());
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }, [client]);

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Smart Telescope</Text>
        <View style={[styles.dot, { backgroundColor: state.last_solve_utc ? colors.success : colors.muted }]} />
      </View>

      <View style={styles.tabs}>
        {(["connect", "status", "history"] as Tab[]).map((name) => (
          <Pressable key={name} onPress={() => setTab(name)}
                     style={[styles.tab, tab === name && styles.tabActive]}>
            <Text style={[styles.tabLabel, tab === name && { color: colors.text }]}>{name}</Text>
          </Pressable>
        ))}
      </View>

      {error ? (
        <View style={[styles.card, { borderColor: colors.danger }]}>
          <Text style={{ color: colors.danger }}>{error}</Text>
        </View>
      ) : null}

      <ScrollView contentContainerStyle={{ gap: space.md, padding: space.md }}>
        {tab === "connect" && (
          <View style={styles.card}>
            <Field label="Broker host" value={host} onChange={setHost} />
            <Field label="MQTT user" value={user} onChange={setUser} />
            <Field label="MQTT password" value={password} onChange={setPassword} secure />
            <Field label="Dashboard API token" value={token} onChange={setToken} secure />
            <Button label="Connect" onPress={connect} />
          </View>
        )}

        {tab === "status" && (
          <>
            <View style={styles.card}>
              <Metric label="RA" value={`${state.ra_deg.toFixed(4)}°`} />
              <Metric label="Dec" value={`${state.dec_deg.toFixed(4)}°`} />
              <Metric label="Pointing error" value={`${state.error_arcmin.toFixed(2)}′`}
                      appearance={state.error_arcmin < 5 ? "success" : "warning"} />
              <Metric label="Latency" value={`${state.latency_ms.toFixed(0)} ms`} />
              <Metric label="Stars" value={String(state.n_stars)} />
            </View>
            <Button label={busy ? "Calibrating…" : "Calibrate now"}
                    onPress={calibrate} disabled={busy} />
          </>
        )}

        {tab === "history" && (
          <>
            <Button label="Refresh" onPress={loadHistory} disabled={busy} />
            {busy ? <ActivityIndicator color={colors.primary} /> : null}
            <View style={styles.card}>
              {episodes.length === 0 ? (
                <Text style={{ color: colors.muted }}>No episodes loaded.</Text>
              ) : episodes.slice(-20).reverse().map((e) => (
                <View key={e.t} style={styles.row}>
                  <Text style={{ color: colors.muted, fontVariant: ["tabular-nums"] }}>
                    {new Date(e.t * 1000).toLocaleTimeString()}
                  </Text>
                  <View style={[styles.bar, { width: Math.min(e.error_arcmin * 8, 140) }]} />
                  <Text style={{ color: colors.text }}>{e.error_arcmin.toFixed(1)}′</Text>
                </View>
              ))}
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function Field({ label, value, onChange, secure }: {
  label: string; value: string; onChange: (v: string) => void; secure?: boolean;
}) {
  return (
    <View style={{ gap: space.xs }}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        secureTextEntry={secure}
        autoCapitalize="none"
        autoCorrect={false}
        placeholderTextColor={colors.muted}
        style={styles.input}
      />
    </View>
  );
}

function Metric({ label, value, appearance = "primary" }: {
  label: string; value: string; appearance?: Appearance;
}) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={{ color: appearanceColor(appearance), fontSize: fontSize.lg,
                     fontVariant: ["tabular-nums"] }}>{value}</Text>
    </View>
  );
}

function Button({ label, onPress, disabled }: {
  label: string; onPress: () => void; disabled?: boolean;
}) {
  return (
    <Pressable onPress={onPress} disabled={disabled}
               style={[styles.button, disabled && { opacity: 0.5 }]}>
      <Text style={styles.buttonLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between",
            paddingHorizontal: space.md, paddingTop: space.md },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "600" },
  dot: { width: 10, height: 10, borderRadius: radius.pill },
  tabs: { flexDirection: "row", gap: space.xs, padding: space.md },
  tab: { flex: 1, paddingVertical: space.sm, borderRadius: radius.rounded,
         borderWidth: 1, borderColor: colors.border, alignItems: "center" },
  tabActive: { backgroundColor: colors.surface, borderColor: colors.primary },
  tabLabel: { color: colors.muted, fontSize: fontSize.sm, textTransform: "capitalize" },
  card: { backgroundColor: colors.surface, borderRadius: radius.rounded,
          borderWidth: 1, borderColor: colors.border, padding: space.md, gap: space.sm },
  label: { color: colors.muted, fontSize: fontSize.sm },
  input: { color: colors.text, backgroundColor: colors.bg, borderRadius: radius.rounded,
           borderWidth: 1, borderColor: colors.border, padding: space.sm,
           fontSize: fontSize.md },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between",
         gap: space.sm },
  button: { backgroundColor: colors.primary, borderRadius: radius.rounded,
            paddingVertical: space.md, alignItems: "center" },
  buttonLabel: { color: "#04121f", fontSize: fontSize.md, fontWeight: "600" },
  bar: { height: 8, borderRadius: radius.pill, backgroundColor: colors.primary, flexGrow: 0 },
});
