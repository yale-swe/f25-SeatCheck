// app/(tabs)/index.tsx
import { useEffect } from "react";
import { useRouter } from "expo-router";
import { Platform } from "react-native";

export default function HomeRedirect() {
  const router = useRouter();

  useEffect(() => {
    // On mount, redirect immediately to the login page
    if (Platform.OS === "web") {
      window.location.replace("/login");
    } else {
      router.replace("/login");
    }
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h2>SeatCheck</h2>
      <p>Redirecting to login...</p>
    </div>
  );
}
