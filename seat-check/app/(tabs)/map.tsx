export default function WebMap() {
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <iframe
        src="http://127.0.0.1:8000/map"
        style={{ border: 0, width: "100%", height: "100%" }}
        title="SeatCheck Map"
      />
    </div>
  );
}
