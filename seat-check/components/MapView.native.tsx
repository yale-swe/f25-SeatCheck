// seat-check/components/MapView.native.tsx
import { useEffect, useState, useCallback } from "react";
import { View, Text, ActivityIndicator, Pressable, Platform } from "react-native";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import * as Linking from "expo-linking";
import { API } from "@/constants/api";

type Venue = {
  id: number;
  name: string;
  lat: number;
  lon: number;
  capacity: number | null;
  occupancy: number | null;
  ratio: number | null;
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
      const { addAuthHeaders } = await import("@/constants/api");
      const res = await fetch(API.venues, {
        credentials: "include" as RequestCredentials,
        headers: addAuthHeaders(),
      });
      if (res.status === 401) {
        setUnauthorized(true);
        setVenues([]);
      } else if (res.ok) {
        const data: Venue[] = await res.json();
        setVenues(data);
      } else {
        setVenues([]);
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

  const checkIn = useCallback(
    async (venueId: number) => {
      try {
        const { addAuthHeaders } = await import("@/constants/api");
        const res = await fetch(API.checkins, {
          method: "POST",
          headers: addAuthHeaders({ "Content-Type": "application/json" }),
          credentials: "include" as RequestCredentials,
          body: JSON.stringify({ venue_id: venueId }),
        });
        if (res.status === 401) {
          setUnauthorized(true);
          return;
        }
        await fetchVenues();
      } catch {
        // noop; could add a toast here
      }
    },
    [fetchVenues]
  );

  const openDevLogin = useCallback(async () => {
    // On native, open dev login in the system browser so the server session cookie is set there.
    await Linking.openURL(`${process.env.EXPO_PUBLIC_API_BASE ?? "http://127.0.0.1:8000"}/auth/dev/login?netid=dev001`);
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
          You’re not authenticated. On native, cookie sessions don’t carry over by default.
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
      {(venues ?? []).map((v) => {
        const ratio = typeof v.ratio === "number" ? v.ratio : 0;
        return (
          <Marker
            key={v.id}
            coordinate={{ latitude: v.lat, longitude: v.lon }}
            title={v.name}
            description={`${v.occupancy ?? 0}/${v.capacity ?? 0} occupied (${Math.round(ratio * 100)}%)`}
            pinColor={colorFor(ratio)}
            onCalloutPress={() => checkIn(v.id)}
          />
        );
      })}
    </MapView>
  );
}
