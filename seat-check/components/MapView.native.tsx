// seat-check/components/MapView.native.tsx
import { useEffect, useState, useCallback } from "react";
import { View, Text, ActivityIndicator, Pressable } from "react-native";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import * as Linking from "expo-linking";

const API = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

type Venue = {
  id: number;
  name: string;
  lat: number;
  lon: number;
  capacity: number;
  occupancy: number;
  ratio: number;
};

function colorFor(ratio: number) {
  if (ratio <= 0.25) return "#2ecc71";
  if (ratio <= 0.5) return "#bada55";
  if (ratio <= 0.75) return "#f1c40f";
  if (ratio <= 1.0) return "#e67e22";
  return "#e74c3c";
}

export default function MapViewNative() {
  const [venues, setVenues] = useState<Venue[] | null>(null);
  const [unauthorized, setUnauthorized] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchVenues = useCallback(async () => {
    setLoading(true);
    setUnauthorized(false);
    try {
      const res = await fetch(`${API}/venues/with_occupancy`, {
        // RN fetch doesn’t truly support cookies like the browser.
        // This is here for future compatibility once we add token auth.
        credentials: "include" as RequestCredentials,
      });
      if (res.status === 401) {
        setUnauthorized(true);
        setVenues([]);
      } else {
        const data: Venue[] = await res.json();
        setVenues(data);
      }
    } catch {
      setVenues([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVenues();
    const id = setInterval(fetchVenues, 15000);
    return () => clearInterval(id);
  }, [fetchVenues]);

  const checkIn = useCallback(async (venueId: number) => {
    try {
      const res = await fetch(`${API}/checkins`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include" as RequestCredentials,
        body: JSON.stringify({ venue_id: venueId }),
      });
      if (res.status === 401) {
        setUnauthorized(true);
        return;
      }
      await fetchVenues();
    } catch {
      // swallow for now; you could show a toast here
    }
  }, [fetchVenues]);

  // Temporary helper: open dev login in system browser (cookie session is browser-only)
  const openDevLogin = useCallback(async () => {
    await Linking.openURL(`${API}/auth/dev/login?netid=dev001`);
  }, []);

  if (loading && !venues) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator />
      </View>
    );
  }

  if (unauthorized) {
    return (
      <View style={{ flex: 1, padding: 16, gap: 12, alignItems: "center", justifyContent: "center" }}>
        <Text style={{ textAlign: "center", fontSize: 16 }}>
          You’re not authenticated. On mobile, cookie sessions don’t carry over by default.
        </Text>
        <Pressable
          onPress={openDevLogin}
          style={{ backgroundColor: "#111", paddingHorizontal: 14, paddingVertical: 10, borderRadius: 8 }}
        >
          <Text style={{ color: "#fff" }}>Open Dev Login in Browser</Text>
        </Pressable>
        <Pressable
          onPress={fetchVenues}
          style={{ borderColor: "#111", borderWidth: 1, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 8 }}
        >
          <Text>Retry</Text>
        </Pressable>
        <Text style={{ opacity: 0.7, textAlign: "center", fontSize: 13 }}>
          (We’ll switch to token auth soon so native works seamlessly.)
        </Text>
      </View>
    );
  }

  const initialRegion = {
    latitude: 41.309,
    longitude: -72.927,
    latitudeDelta: 0.02,
    longitudeDelta: 0.02,
  };

  return (
    <MapView
      style={{ flex: 1 }}
      provider={PROVIDER_GOOGLE}
      initialRegion={initialRegion}
    >
      {(venues ?? []).map((v) => (
        <Marker
          key={v.id}
          coordinate={{ latitude: v.lat, longitude: v.lon }}
          title={v.name}
          description={`${v.occupancy}/${v.capacity} occupied (${Math.round((v.ratio || 0) * 100)}%)`}
          pinColor={colorFor(v.ratio || 0)}
          // Pressing the callout triggers a check-in (temporary, can swap for a custom callout)
          onCalloutPress={() => checkIn(v.id)}
        />
      ))}
    </MapView>
  );
}
