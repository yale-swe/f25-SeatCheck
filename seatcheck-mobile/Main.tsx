// SeatCheck – MVP UI (React Native + Expo)
// Tabs: Home (tiles), Map, Check In, Settings

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Appearance,
  FlatList,
  Image,
  Linking,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { NavigationContainer, DefaultTheme, DarkTheme } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { Ionicons } from "@expo/vector-icons";
dayjs.extend(relativeTime);

let MapView: any = null;
let Heatmap: any = null;
let Marker: any = null;
let PROVIDER_GOOGLE: any = null;
// Loose type so TS is happy on web:
type Region = any;

// Types
type NoiseLevel = "silent" | "quiet" | "moderate" | "loud";
type LocationAmenity =
  | "outlets"
  | "whiteboards"
  | "printers"
  | "windows"
  | "group rooms"
  | "bathrooms nearby"
  | "food nearby";
type AccessibilityTag = "wheelchair" | "elevator" | "automatic doors" | "accessible restrooms";

type LocationItem = {
  id: string;
  name: string;
  category: "library" | "cafe" | "lounge" | "classroom";
  lat: number;
  lng: number;
  capacity_estimate?: number;
  imageUrl?: string;
  amenities: LocationAmenity[];
  accessibility: AccessibilityTag[];
  updated_at?: string;
  current?: { avg_occupancy: number; noise: NoiseLevel; checkins_count: number };
};

type CheckInPayload = {
  location_id: string;
  occupancy_level: number; // 0-5
  noise_level: NoiseLevel;
  outlets_free_pct?: number;
};

// Config
const API_BASE = "https://api.seatcheck.local/v1"; // placeholder
const YALE_CAMPUS = {
  latitude: 41.3102,
  longitude: -72.9267,
  latitudeDelta: 0.02,
  longitudeDelta: 0.02,
};
const IMAGE_FALLBACK =
  "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1200&q=70&auto=format&fit=crop";

// Seed demo data (replace with /v1/locations)
const SEED_LOCATIONS: LocationItem[] = [
  {
    id: "sterling",
    name: "Sterling Memorial Library",
    category: "library",
    lat: 41.3114,
    lng: -72.9279,
    capacity_estimate: 800,
    imageUrl: IMAGE_FALLBACK,
    amenities: ["outlets", "whiteboards", "windows"],
    accessibility: ["wheelchair", "elevator", "accessible restrooms"],
    updated_at: new Date().toISOString(),
    current: { avg_occupancy: 3.2, noise: "quiet", checkins_count: 128 },
  },
  {
    id: "bass",
    name: "Bass Library",
    category: "library",
    lat: 41.3111,
    lng: -72.9296,
    capacity_estimate: 500,
    imageUrl: IMAGE_FALLBACK,
    amenities: ["outlets", "whiteboards"],
    accessibility: ["wheelchair", "elevator"],
    updated_at: new Date().toISOString(),
    current: { avg_occupancy: 2.6, noise: "moderate", checkins_count: 92 },
  },
  {
    id: "sc",
    name: "Schwarzman Center Lounge",
    category: "lounge",
    lat: 41.30882,
    lng: -72.9261,
    capacity_estimate: 250,
    imageUrl: IMAGE_FALLBACK,
    amenities: ["food nearby", "outlets"],
    accessibility: ["wheelchair", "automatic doors"],
    updated_at: new Date().toISOString(),
    current: { avg_occupancy: 4.1, noise: "loud", checkins_count: 61 },
  },
];

// Auth context (CAS hookup later)
const AuthContext = React.createContext<{
  token: string | null;
  setToken: (t: string | null) => void;
} | null>(null);

function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// API helpers
async function apiFetch<T>(path: string, token?: string | null, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function fetchLocationsStub(): Promise<LocationItem[]> {
  await wait(300);
  return SEED_LOCATIONS;
}
async function fetchLocationDetailsStub(id: string): Promise<LocationItem> {
  await wait(250);
  const x = SEED_LOCATIONS.find((l) => l.id === id);
  if (!x) throw new Error("Not found");
  return x;
}
async function submitCheckInStub(payload: CheckInPayload): Promise<{ ok: true }> {
  await wait(250);
  const idx = SEED_LOCATIONS.findIndex((l) => l.id === payload.location_id);
  if (idx >= 0) {
    const c = SEED_LOCATIONS[idx].current || { avg_occupancy: 0, noise: "moderate", checkins_count: 0 };
    const next = (c.avg_occupancy * c.checkins_count + payload.occupancy_level) / (c.checkins_count + 1);
    SEED_LOCATIONS[idx].current = {
      avg_occupancy: Number(next.toFixed(1)),
      noise: payload.noise_level,
      checkins_count: c.checkins_count + 1,
    };
    SEED_LOCATIONS[idx].updated_at = new Date().toISOString();
  }
  return { ok: true };
}

// Realtime stub
function useRealtime(_onMessage: (msg: any) => void, _token?: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    // Wire when backend ws is ready
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);
  return wsRef;
}

// UI atoms
function Pill({ children }: { children: React.ReactNode }) {
  return (
    <View style={styles.pill}>
      <Text style={styles.pillText}>{children}</Text>
    </View>
  );
}
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ marginBottom: 16 }}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={{ gap: 8 }}>{children}</View>
    </View>
  );
}
function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.statBox}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

// Screens
function HomeScreen({ navigation }: any) {
  const [locations, setLocations] = useState<LocationItem[] | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchLocationsStub()
      .then((d) => mounted && setLocations(d))
      .catch((e) => Alert.alert("Load failed", String(e)));
    return () => {
      mounted = false;
    };
  }, []);

  const renderItem = useCallback(
    ({ item }: { item: LocationItem }) => (
      <View style={styles.tile}>
        {expandedId === item.id && (
          <View style={styles.keycard}>
            <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
              <Stat label="Max" value={item.capacity_estimate ?? "—"} />
              <Stat label="Noise" value={item.current?.noise ?? "—"} />
              <Stat label="Occupancy" value={(item.current?.avg_occupancy ?? 0).toFixed(1)} />
            </View>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
              {item.amenities.map((a) => (
                <Pill key={a}>{a}</Pill>
              ))}
            </View>
            <View style={{ flexDirection: "row", justifyContent: "flex-end", marginTop: 8, gap: 8 }}>
              <TouchableOpacity onPress={() => navigation.navigate("Details", { id: item.id })} style={styles.linkBtn}>
                <Text style={styles.linkBtnText}>More details</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => navigation.navigate("CheckIn", { id: item.id })} style={styles.linkBtn}>
                <Text style={styles.linkBtnText}>Check in</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        <Image source={{ uri: item.imageUrl || IMAGE_FALLBACK }} style={styles.tileImage} resizeMode="cover" />
        <Pressable onPress={() => setExpandedId(expandedId === item.id ? null : item.id)}>
          <Text style={styles.tileTitle}>{item.name}</Text>
        </Pressable>
      </View>
    ),
    [expandedId]
  );

  if (!locations) {
    return (
      <SafeAreaView style={styles.screen}>
        <ActivityIndicator style={{ marginTop: 24 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <TextInput placeholder="Search study spots…" style={styles.search} accessibilityLabel="Search" />
      <FlatList
        data={locations}
        keyExtractor={(it) => it.id}
        numColumns={2}
        contentContainerStyle={{ padding: 12, gap: 12 }}
        columnWrapperStyle={{ gap: 12 }}
        renderItem={renderItem}
      />
    </SafeAreaView>
  );
}

function MapScreen({ navigation }: any) {
  const [region, setRegion] = useState<Region>(YALE_CAMPUS as Region);
  const [locations, setLocations] = useState<LocationItem[] | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchLocationsStub().then((d) => mounted && setLocations(d));
    return () => {
      mounted = false;
    };
  }, []);

  const heatPoints = useMemo(
    () =>
      (locations || []).map((l) => ({
        latitude: l.lat,
        longitude: l.lng,
        weight: Math.max(0.1, l.current?.avg_occupancy ?? 0.1),
      })),
    [locations]
  );

  // Web fallback
  if (Platform.OS === "web") {
    return (
      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
        <Text style={{ fontSize: 18, fontWeight: "800", marginBottom: 8 }}>Map preview not available on web</Text>
        <Text style={{ color: "#374151", marginBottom: 12 }}>
          Use the iOS Simulator (press <Text style={{ fontWeight: "800" }}>i</Text> in the Expo terminal) or Expo Go on your phone to
          see the interactive map.
        </Text>
        <Section title="Nearby places">
          {(locations || []).map((l) => (
            <View
              key={l.id}
              style={{ paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: "#e5e7eb" }}
            >
              <Text style={{ fontWeight: "800" }}>{l.name}</Text>
              <Text style={{ color: "#6b7280" }}>
                Occ {(l.current?.avg_occupancy ?? 0).toFixed(1)} · {l.current?.noise ?? "n/a"}
              </Text>
              <TouchableOpacity
                onPress={() => navigation.navigate("Details", { id: l.id })}
                style={[styles.linkBtn, { marginTop: 6, alignSelf: "flex-start" }]}
              >
                <Text style={styles.linkBtnText}>Open details</Text>
              </TouchableOpacity>
            </View>
          ))}
        </Section>
      </ScrollView>
    );
  }

  // Native map
  return (
    <View style={{ flex: 1 }}>
      {MapView ? (
        <MapView
          style={{ flex: 1 }}
          provider={PROVIDER_GOOGLE}
          initialRegion={region}
          onRegionChangeComplete={setRegion}
        >
          {heatPoints.length > 0 && Heatmap && <Heatmap points={heatPoints as any} radius={40} opacity={0.6} />}
          {(locations || []).map((l) => (
            <Marker
              key={l.id}
              coordinate={{ latitude: l.lat, longitude: l.lng }}
              title={l.name}
              description={`Occ ${l.current?.avg_occupancy ?? 0}/5, ${l.current?.noise ?? "n/a"}`}
              onPress={() => navigation.navigate("Details", { id: l.id })}
            />
          ))}
        </MapView>
      ) : (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <Text>Map module not loaded.</Text>
        </View>
      )}
    </View>
  );
}

function DetailsScreen({ route, navigation }: any) {
  const { id } = route.params as { id: string };
  const [item, setItem] = useState<LocationItem | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchLocationDetailsStub(id)
      .then((d) => mounted && setItem(d))
      .catch((e) => Alert.alert("Failed to load", String(e)));
    return () => {
      mounted = false;
    };
  }, [id]);

  if (!item) {
    return (
      <SafeAreaView style={styles.screen}>
        <ActivityIndicator style={{ marginTop: 24 }} />
      </SafeAreaView>
    );
  }

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
      <Image source={{ uri: item.imageUrl || IMAGE_FALLBACK }} style={styles.detailImage} />
      <Text style={styles.detailTitle}>{item.name}</Text>
      <View style={{ flexDirection: "row", gap: 8, marginBottom: 12 }}>
        <Pill>{item.category}</Pill>
        <Pill>Updated {dayjs(item.updated_at).fromNow()}</Pill>
      </View>

      <Section title="Current status">
        <View style={{ flexDirection: "row", gap: 8, justifyContent: "space-between" }}>
          <Stat label="Occupancy" value={(item.current?.avg_occupancy ?? 0).toFixed(1)} />
          <Stat label="Noise" value={item.current?.noise ?? "—"} />
          <Stat label="Check-ins" value={item.current?.checkins_count ?? 0} />
        </View>
      </Section>

      <Section title="Amenities">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {item.amenities.map((a) => (
            <Pill key={a}>{a}</Pill>
          ))}
        </View>
      </Section>

      <Section title="Accessibility">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {item.accessibility.map((a) => (
            <Pill key={a}>{a}</Pill>
          ))}
        </View>
      </Section>

      <View style={{ flexDirection: "row", gap: 12, marginTop: 12 }}>
        <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate("CheckIn", { id: item.id })}>
          <Text style={styles.primaryBtnText}>Check in</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() =>
            Linking.openURL("https://registrar.yale.edu/yale-university-classrooms/classroom-list")
          }
        >
          <Text style={styles.secondaryBtnText}>Room info</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

function CheckInScreen({ route, navigation }: any) {
  const { id } = (route.params || {}) as { id?: string };
  const [selectedId, setSelectedId] = useState<string | undefined>(id);
  const [occupancy, setOccupancy] = useState(3);
  const [noise, setNoise] = useState<NoiseLevel>("moderate");
  const [busy, setBusy] = useState(false);

  const locations = SEED_LOCATIONS;

  const submit = async () => {
    if (!selectedId) return Alert.alert("Pick a location", "Please choose where you are.");
    try {
      setBusy(true);
      await submitCheckInStub({ location_id: selectedId, occupancy_level: occupancy, noise_level: noise });
      Alert.alert("Thanks!", "Your check-in was submitted.");
      navigation.navigate("Details", { id: selectedId });
    } catch (e: any) {
      Alert.alert("Submit failed", String(e?.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16, gap: 16 }}>
      <Section title="Location">
        <View style={styles.selectBox}>
          <Text style={styles.selectLabel}>Choose a place</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            {locations.map((l) => (
              <TouchableOpacity
                key={l.id}
                style={[styles.choiceChip, selectedId === l.id && styles.choiceChipActive]}
                onPress={() => setSelectedId(l.id)}
              >
                <Text style={[styles.choiceChipText, selectedId === l.id && styles.choiceChipTextActive]}>{l.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Section>

      <Section title="Occupancy (0–5)">
        <View style={styles.sliderRow}>
          {[0, 1, 2, 3, 4, 5].map((n) => (
            <TouchableOpacity
              key={n}
              style={[styles.sliderDot, occupancy === n && styles.sliderDotActive]}
              onPress={() => setOccupancy(n)}
            >
              <Text style={[styles.sliderDotText, occupancy === n && styles.sliderDotTextActive]}>{n}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.helperText}>0 empty · 1 very light · 2 light · 3 moderate · 4 crowded · 5 packed</Text>
      </Section>

      <Section title="Noise">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {(["silent", "quiet", "moderate", "loud"] as NoiseLevel[]).map((lvl) => (
            <TouchableOpacity
              key={lvl}
              style={[styles.choiceChip, noise === lvl && styles.choiceChipActive]}
              onPress={() => setNoise(lvl)}
            >
              <Text style={[styles.choiceChipText, noise === lvl && styles.choiceChipTextActive]}>{lvl}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </Section>

      <TouchableOpacity style={[styles.primaryBtn, busy && { opacity: 0.6 }]} disabled={busy} onPress={submit}>
        <Text style={styles.primaryBtnText}>{busy ? "Submitting…" : "Submit check-in"}</Text>
      </TouchableOpacity>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

function SettingsScreen() {
  const [trackLocation, setTrackLocation] = useState(true);
  const colorScheme = Appearance.getColorScheme();
  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16, gap: 16 }}>
      <Section title="Preferences">
        <TouchableOpacity style={styles.toggleRow} onPress={() => setTrackLocation((v) => !v)}>
          <Text style={styles.toggleLabel}>Location tracking</Text>
          <View style={[styles.toggle, trackLocation && styles.toggleOn]}>
            <View style={[styles.knob, trackLocation && styles.knobOn]} />
          </View>
        </TouchableOpacity>
        <Text style={styles.helperText}>
          Used to center the map and improve recommendations. Never shares exact coordinates publicly.
        </Text>
      </Section>

      <Section title="Appearance">
        <Text style={styles.bodyText}>Theme follows your device setting ({colorScheme}). Dark mode supported.</Text>
      </Section>

      <Section title="Privacy">
        <Text style={styles.bodyText}>
          Check-ins are anonymous by default. Friend presence (future) is opt-in and shown only at the place level.
        </Text>
      </Section>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

// ---------- Navigation ----------
const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function Tabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: "#2563eb",
        tabBarLabelStyle: { fontSize: 12 },
        tabBarIcon: ({ color, size }) => {
          const map: Record<string, keyof typeof Ionicons.glyphMap> = {
            Home: "home-outline",
            Map: "map-outline",
            CheckIn: "checkmark-done-outline",
            Settings: "settings-outline",
          };
          const icon = map[route.name] || "ellipse-outline";
          return <Ionicons name={icon} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Map" component={MapScreen} />
      <Tab.Screen name="CheckIn" component={CheckInScreen} options={{ title: "Check In" }} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const scheme = Appearance.getColorScheme();

  return (
    <AuthContext.Provider value={{ token, setToken }}>
      <NavigationContainer theme={scheme === "dark" ? DarkTheme : DefaultTheme}>
        <StatusBar barStyle={scheme === "dark" ? "light-content" : "dark-content"} />
        <Stack.Navigator>
          <Stack.Screen name="Root" component={Tabs} options={{ headerShown: false }} />
          <Stack.Screen name="Details" component={DetailsScreen} options={{ title: "Details" }} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthContext.Provider>
  );
}

// Styles
const styles = StyleSheet.create({
  screen: { flex: 1 },
  search: {
    margin: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "#d1d5db",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: "#fff",
  },
  tile: {
    flex: 1,
    backgroundColor: "#fff",
    borderRadius: 16,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  keycard: {
    padding: 12,
    backgroundColor: "#f8fafc",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#e5e7eb",
  },
  linkBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#e5e7eb",
  },
  linkBtnText: { fontWeight: "600" },
  tileImage: { width: "100%", height: 140 },
  tileTitle: { fontSize: 16, fontWeight: "700", padding: 12 },

  sectionTitle: { fontSize: 18, fontWeight: "800", marginBottom: 6 },
  statBox: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: "#fff",
    borderRadius: 12,
    flex: 1,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "#e5e7eb",
  },
  statValue: { fontSize: 18, fontWeight: "800" },
  statLabel: { fontSize: 12, color: "#6b7280" },
  pill: { paddingHorizontal: 10, paddingVertical: 6, backgroundColor: "#eef2ff", borderRadius: 999 },
  pillText: { fontSize: 12, fontWeight: "700", color: "#3730a3" },

  detailImage: { width: "100%", height: 220, borderRadius: 16, marginBottom: 12 },
  detailTitle: { fontSize: 24, fontWeight: "900", marginBottom: 8 },
  primaryBtn: { backgroundColor: "#2563eb", paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12 },
  primaryBtnText: { color: "#fff", fontWeight: "800", textAlign: "center" },
  secondaryBtn: { backgroundColor: "#e5e7eb", paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12 },
  secondaryBtnText: { color: "#111827", fontWeight: "800" },

  selectBox: {
    padding: 12,
    backgroundColor: "#fff",
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "#e5e7eb",
  },
  selectLabel: { fontSize: 14, color: "#374151", marginBottom: 8 },
  choiceChip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: "#f3f4f6" },
  choiceChipActive: { backgroundColor: "#dbeafe" },
  choiceChipText: { fontWeight: "700", color: "#374151" },
  choiceChipTextActive: { color: "#1e3a8a" },

  sliderRow: { flexDirection: "row", gap: 8 },
  sliderDot: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: "#f3f4f6",
    alignItems: "center",
  },
  sliderDotActive: { backgroundColor: "#dbeafe" },
  sliderDotText: { fontWeight: "800", color: "#374151" },
  sliderDotTextActive: { color: "#1e3a8a" },

  helperText: { fontSize: 12, color: "#6b7280" },

  toggleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 8 },
  toggleLabel: { fontSize: 16, fontWeight: "700" },
  toggle: { width: 54, height: 32, borderRadius: 999, backgroundColor: "#e5e7eb", padding: 4 },
  toggleOn: { backgroundColor: "#93c5fd" },
  knob: { width: 24, height: 24, borderRadius: 12, backgroundColor: "#fff" },
  knobOn: { marginLeft: 22 },

  bodyText: { fontSize: 14, color: "#111827" },
});
