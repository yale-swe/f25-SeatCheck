// seat-check/components/MapView.web.tsx
const API = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function MapView() {
  const src = `${API}/map`;
  return (
    <div style={{ position: "fixed", inset: 0, height: "100vh" }}>
      <iframe
        src={src}
        title="SeatCheck Map"
        style={{ border: 0, width: "100%", height: "100%" }}
      />
    </div>
  );
}
