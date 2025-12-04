// app/login.tsx
import { useEffect, useState } from "react";
import { Platform, TextInput, View } from "react-native";
import { Link } from "expo-router";
import * as Linking from "expo-linking";

const API = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

type Me = { netid: string };

export default function Login() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDev, setShowDev] = useState(false);
  const [netid, setNetid] = useState("dev001");

  const demoUsers = ["dev001", "cs1234", "ay123", "yx999", "testnetid"];

  useEffect(() => {
    // Check for token in URL (from redirect after dev login)
    if (Platform.OS === "web" && typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token");
      if (token) {
        console.log("[Login] Found token in URL, storing in localStorage");
        localStorage.setItem("seatcheck_auth_token", token);
        // Remove token from URL
        window.history.replaceState({}, "", window.location.pathname);
      }
    }

    console.log("[Login] Checking auth status...");
    const token = typeof window !== "undefined" ? localStorage.getItem("seatcheck_auth_token") : null;
    const headers: HeadersInit = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    fetch(`${API}/auth/me`, { 
      credentials: "include",
      headers,
    })
      .then((r) => {
        console.log(`[Login] /auth/me response: ${r.status} ${r.statusText}`);
        if (r.ok) {
          return r.json();
        } else {
          console.log(`[Login] Auth check failed: ${r.status}`);
          // Clear invalid token
          if (token && typeof window !== "undefined") {
            localStorage.removeItem("seatcheck_auth_token");
          }
          return null;
        }
      })
      .then((data) => {
        console.log(`[Login] Auth result:`, data);
        setMe(data);
      })
      .catch((err) => {
        console.error("[Login] Auth check error:", err);
        setMe(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const startCAS = () => {
    const url = `${API}/auth/cas/login`;
    if (Platform.OS === "web") window.location.assign(url);
    else Linking.openURL(url);
  };

  const devLogin = (chosen?: string) => {
    const who = (chosen ?? netid).trim();
    if (!who) return;
    const url = `${API}/auth/dev/login?netid=${encodeURIComponent(who)}`;
    console.log(`[Login] Dev login: navigating to ${url}`);
    if (Platform.OS === "web") {
      window.location.assign(url);
    } else {
      Linking.openURL(url);
    }
  };

  const containerStyle: React.CSSProperties = {
    backgroundColor: "#fff",
    color: "#000",
    minHeight: "100vh",
    padding: 24,
    fontFamily: "system-ui, sans-serif",
  };

  const buttonStyle: React.CSSProperties = {
    padding: "10px 14px",
    borderRadius: 8,
    border: "1px solid #111",
    background: "#111",
    color: "#fff",
    cursor: "pointer",
  };

  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    background: "transparent",
    color: "#111",
    border: "1px dashed #666",
    marginLeft: 8,
  };

  if (loading) {
    return (
      <div style={containerStyle}>
        <h2>SeatCheck</h2>
        <p>Checking your session…</p>
      </div>
    );
  }

  if (me) {
    return (
      <div style={containerStyle}>
        <h2>Logged in as {me.netid}</h2>
        <p>Great — you can open the live map.</p>
        <Link href="/(tabs)/map">Go to Map</Link>
        <br />
        <br />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            // Clear token from localStorage
            if (typeof window !== "undefined") {
              localStorage.removeItem("seatcheck_auth_token");
            }
            fetch(`${API}/auth/logout`, {
              method: "POST",
              credentials: "include",
            })
              .then(() => (window.location.href = "/login"))
              .catch(() => (window.location.href = "/login"));
          }}
        >
          <button type="submit" style={buttonStyle}>
            Log out
          </button>
        </form>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h2>SeatCheck</h2>
      <p>You must sign in with Yale CAS to continue.</p>

      {/* CAS login */}
      <button onClick={startCAS} style={buttonStyle}>
        Log in with Yale CAS
      </button>

      {/* Dev panel toggle */}
      <button onClick={() => setShowDev((s) => !s)} style={secondaryButtonStyle}>
        Dev sign-in
      </button>

      {/* Dev sign-in panel */}
      {showDev && (
        <div
          style={{
            marginTop: 16,
            padding: 16,
            border: "1px solid #ddd",
            borderRadius: 12,
            background: "#fafafa",
            color: "#000",
          }}
        >
          <p style={{ marginTop: 0 }}>
            <strong>Sign in without CAS (for development)</strong>
          </p>
          <div style={{ marginBottom: 8 }}>
            {demoUsers.map((u) => (
              <button
                key={u}
                onClick={() => devLogin(u)}
                style={{
                  marginRight: 6,
                  marginBottom: 6,
                  padding: "6px 10px",
                  borderRadius: 8,
                  border: "1px solid #ccc",
                  background: "#fff",
                  cursor: "pointer",
                }}
              >
                {u}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <View style={{ flex: 1, minWidth: 220 }}>
              <TextInput
                value={netid}
                onChangeText={setNetid}
                placeholder="Enter netid…"
                autoCapitalize="none"
                style={{
                  padding: 10,
                  borderWidth: 1,
                  borderColor: "#ccc",
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: "#fff",
                  color: "#000",
                }}
              />
            </View>
            <button
              onClick={() => devLogin()}
              style={{ ...buttonStyle, padding: "8px 12px" }}
            >
              Sign in as netid
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
