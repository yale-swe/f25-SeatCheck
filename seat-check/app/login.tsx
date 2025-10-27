// app/login.tsx
import { useEffect, useState } from "react";
import { Platform } from "react-native";
import { Link, router } from "expo-router";
import * as Linking from "expo-linking";

const API =
  process.env.EXPO_PUBLIC_API_BASE ??
  "http://127.0.0.1:8000"; // override per env when needed

type Me = { netid: string };

export default function Login() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then(async (r) => {
        if (!r.ok) return null;
        return (await r.json()) as Me;
      })
      .then((data) => setMe(data))
      .catch(() => setMe(null))
      .finally(() => setLoading(false));
  }, []);

  const startCAS = () => {
    const url = `${API}/auth/cas/login`;
    if (Platform.OS === "web") {
      // Full-page nav is important so the CAS cookies/redirects behave
      window.location.assign(url);
    } else {
      // Open CAS in system browser (simple approach for native dev)
      Linking.openURL(url);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <h2>SeatCheck</h2>
        <p>Checking your session…</p>
      </div>
    );
  }

  if (me) {
    return (
      <div style={{ padding: 24 }}>
        <h2>Logged in as {me.netid}</h2>
        {/* Prefer Expo Router navigation */}
        <Link href="/(tabs)/map">Go to Map</Link>
        {/* Or programmatic: <button onClick={() => router.push("/(tabs)/map")}>Go to Map</button> */}
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>SeatCheck</h2>
      <p>You must sign in with Yale CAS to continue.</p>
      <button
        onClick={startCAS}
        style={{
          padding: "8px 12px",
          border: "1px solid #333",
          borderRadius: 6,
          background: "transparent",
          cursor: "pointer",
        }}
      >
        Log in with Yale CAS
      </button>
    </div>
  );
}
