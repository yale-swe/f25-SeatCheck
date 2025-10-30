// app/(tabs)/map.tsx
import { Platform } from "react-native";

const API = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function WebMap() {
  if (Platform.OS !== "web") {
    return (
      <div style={{ padding: 24 }}>
        <h2>SeatCheck</h2>
        <p>Map view available on web version for now.</p>
      </div>
    );
  }

  const src = `${API}/map`;

  return (
    <div style={{ position: "fixed", inset: 0, height: "100vh" }}>
      <iframe
        src={src}
        style={{ border: 0, width: "100%", height: "100%" }}
        title="SeatCheck Map"
      />
    </div>
  );
}
