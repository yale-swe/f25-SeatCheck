// SeatCheck – MVP UI (React Native + Expo) - Main.tsx
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
import type { NavigatorScreenParams } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

// Conditional imports - prevent web breakage
let dayjs: any;
let Ionicons: any;

try {
  dayjs = require("dayjs");
  const relativeTime = require("dayjs/plugin/relativeTime");
  dayjs.extend(relativeTime);
} catch (e) {
  console.warn("dayjs not available:", e);
  dayjs = (date?: any) => ({
    fromNow: () => "recently",
    toISOString: () => new Date().toISOString(),
  });
}

try {
  const icons = require("@expo/vector-icons");
  Ionicons = icons.Ionicons;
} catch (e) {
  console.warn("@expo/vector-icons not available:", e);
  Ionicons = ({ name, size, color }: any) => (
    <View style={{ width: size, height: size, backgroundColor: color, borderRadius: size / 2 }} />
  );
}

// --- Navigation types ---
type RootTabParamList = {
  Home: undefined;
  Map: undefined;
  CheckIn: { id?: string } | undefined;
  Settings: undefined;
};

type RootStackParamList = {
  Root: NavigatorScreenParams<RootTabParamList>;
  Details: { id: string };
};

// Map imports - ONLY for native platforms
let MapView: any = null;
let Heatmap: any = null;
let Marker: any = null;
let PROVIDER_GOOGLE: any = null;

if (Platform.OS !== "web") {
  try {
    const maps = require("react-native-maps");
    MapView = maps.default;
    Marker = maps.Marker;
    PROVIDER_GOOGLE = maps.PROVIDER_GOOGLE;
    Heatmap = maps.Heatmap;
  } catch (e) {
    console.log("react-native-maps not installed (optional for MVP)");
  }
}

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
  occupancy_level: number;
  noise_level: NoiseLevel;
  outlets_free_pct?: number;
};

// Config
const API_BASE = "https://api.seatcheck.local/v1";
const YALE_CAMPUS = {
  latitude: 41.3102,
  longitude: -72.9267,
  latitudeDelta: 0.02,
  longitudeDelta: 0.02,
};
const IMAGE_FALLBACK =
  "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1200&q=70&auto=format&fit=crop";

// Seed data
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

// Auth context
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
  const [query, setQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const filtered = useMemo(() => {
    if (!locations) return [];
    const q = query.trim().toLowerCase();
    if (!q) return locations;
    return locations.filter((l) => l.name.toLowerCase().includes(q) || l.category.toLowerCase().includes(q));
  }, [locations, query]);

  const onRefresh = async () => {
    try {
      setRefreshing(true);
      const next = await fetchLocationsStub();
      setLocations(next);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    fetchLocationsStub()
      .then((d) => mounted && setLocations(d))
      .catch((e) => {
        console.error("Load failed:", e);
        Alert.alert("Load failed", String(e));
      });
    return () => {
      mounted = false;
    };
  }, []);

  const renderItem = useCallback(
    ({ item }: { item: LocationItem }) => (
      <TouchableOpacity
        style={styles.cardStacked}
        onPress={() => setExpandedId(expandedId === item.id ? null : item.id)}
        activeOpacity={0.95}
      >
        <View style={styles.cardContent}>
          {/* Left: Image */}
          <View style={styles.cardImageContainer}>
            <Image source={{ uri: item.imageUrl || IMAGE_FALLBACK }} style={styles.cardImage} resizeMode="cover" />
          </View>

          {/* Right: Info */}
          <View style={styles.cardInfo}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <View style={styles.cardStats}>
              <View style={styles.cardStatItem}>
                <Text style={styles.cardStatLabel}>Occupancy</Text>
                <Text style={styles.cardStatValue}>{(item.current?.avg_occupancy ?? 0).toFixed(1)}/5</Text>
              </View>
              <View style={styles.cardStatDivider} />
              <View style={styles.cardStatItem}>
                <Text style={styles.cardStatLabel}>Noise</Text>
                <Text style={styles.cardStatValue}>{item.current?.noise ?? "—"}</Text>
              </View>
            </View>

            {expandedId === item.id && (
              <View style={styles.cardExpanded}>
                <View style={styles.cardAmenities}>
                  {item.amenities.slice(0, 3).map((a) => (
                    <View key={a} style={styles.amenityChip}>
                      <Text style={styles.amenityChipText}>{a}</Text>
                    </View>
                  ))}
                </View>
                <View style={styles.cardButtons}>
                  <TouchableOpacity onPress={() => navigation.navigate("Details", { id: item.id })} style={styles.cardBtn}>
                    <Text style={styles.cardBtnText}>Details</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => navigation.navigate("CheckIn", { id: item.id })}
                    style={[styles.cardBtn, styles.cardBtnPrimary]}
                  >
                    <Text style={[styles.cardBtnText, styles.cardBtnTextPrimary]}>Check In</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
    ),
    [expandedId, navigation]
  );

  if (!locations) {
    return (
      <SafeAreaView style={styles.screenWithHeader}>
        <View style={styles.header}>
          <Text style={{ fontSize: 28, fontWeight: "900", color: "#1e40af" }}>SeatCheck</Text>
        </View>
        <View style={{ padding: 16, gap: 16 }}>
          {[0, 1, 2].map((i) => (
            <View key={i} style={styles.skeletonCardStacked} />
          ))}
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screenWithHeader}>
      {/* Header with Logo */}
      <View style={styles.header}>
        <Text style={{ fontSize: 28, fontWeight: "900", color: "#1e40af" }}>SeatCheck</Text>
      </View>

      {/* Search */}
      <TextInput
        placeholder="Search study spots…"
        placeholderTextColor="#94a3b8"
        style={styles.searchNew}
        value={query}
        onChangeText={setQuery}
      />

      {/* Locations List */}
      {filtered.length === 0 ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyTitle}>No matching spots</Text>
          <Text style={styles.helperText}>Try another name or category</Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(it) => it.id}
          contentContainerStyle={{ padding: 16, gap: 16 }}
          renderItem={renderItem}
          refreshing={refreshing}
          onRefresh={onRefresh}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

function MapScreen({ navigation }: any) {
  const [region, setRegion] = useState<Region>(YALE_CAMPUS as Region);
  const [locations, setLocations] = useState<LocationItem[] | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchLocationsStub()
      .then((d) => mounted && setLocations(d))
      .catch((e) => console.error("Failed to load locations:", e));
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
  if (Platform.OS === "web" || !MapView) {
    return (
      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
        <Text style={{ fontSize: 18, fontWeight: "800", marginBottom: 8 }}>
          {Platform.OS === "web" ? "Map preview not available on web" : "Map not loaded"}
        </Text>
        <Text style={{ color: "#374151", marginBottom: 12 }}>
          {Platform.OS === "web"
            ? "Use the iOS Simulator or Expo Go on your phone to see the interactive map."
            : "Install react-native-maps: npx expo install react-native-maps"}
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
      <MapView style={{ flex: 1 }} provider={PROVIDER_GOOGLE} initialRegion={region} onRegionChangeComplete={setRegion}>
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
    </View>
  );
}

function DetailsScreen({ route, navigation }: NativeStackScreenProps<RootStackParamList, "Details">) {
  const { id } = route.params;
  const [item, setItem] = useState<LocationItem | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchLocationDetailsStub(id)
      .then((d) => mounted && setItem(d))
      .catch((e) => {
        console.error("Failed to load details:", e);
        Alert.alert("Failed to load", String(e));
      });
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
        <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate("Root", { screen: "CheckIn", params: { id: item.id } })}>
          <Text style={styles.primaryBtnText}>Check in</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => Linking.openURL("https://registrar.yale.edu/yale-university-classrooms/classroom-list")}
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
      console.error("Submit failed:", e);
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

// Navigation
const Tab = createBottomTabNavigator<RootTabParamList>();
const Stack = createNativeStackNavigator<RootStackParamList>();

function Tabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: "#2563eb",
        tabBarLabelStyle: { fontSize: 12 },
        tabBarIcon: ({ color, size }) => {
          const iconMap: Record<string, string> = {
            Home: "home-outline",
            Map: "map-outline",
            CheckIn: "checkmark-done-outline",
            Settings: "settings-outline",
          };
          const iconName = iconMap[route.name] || "ellipse-outline";
          return <Ionicons name={iconName} size={size} color={color} />;
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

export default function Main() {
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
  screen: { flex: 1, backgroundColor: "#f8fafc" },
  screenWithHeader: { flex: 1, backgroundColor: "#f8fafc" },

  // Header with logo
  header: {
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
    alignItems: "center",
  },
  logo: {
    width: 160,
    height: 50,
  },

  // New search style
  searchNew: {
    marginHorizontal: 16,
    marginVertical: 12,
    borderWidth: 1.5,
    borderColor: "#cbd5e1",
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    backgroundColor: "#fff",
    fontWeight: "500",
    color: "#1e293b",
  },

  // Stacked card layout
  cardStacked: {
    backgroundColor: "#fff",
    borderRadius: 20,
    overflow: "hidden",
    shadowColor: "#0f172a",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  cardContent: {
    flexDirection: "row",
    minHeight: 120,
  },
  cardImageContainer: {
    width: 120,
    backgroundColor: "#e2e8f0",
  },
  cardImage: {
    width: "100%",
    height: "100%",
  },
  cardInfo: {
    flex: 1,
    padding: 16,
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0f172a",
    marginBottom: 8,
    letterSpacing: -0.3,
  },
  cardStats: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  cardStatItem: {
    flex: 1,
  },
  cardStatLabel: {
    fontSize: 12,
    color: "#64748b",
    fontWeight: "600",
    marginBottom: 2,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  cardStatValue: {
    fontSize: 17,
    fontWeight: "700",
    color: "#3b82f6",
  },
  cardStatDivider: {
    width: 1,
    height: 32,
    backgroundColor: "#e2e8f0",
  },

  // Expanded card section
  cardExpanded: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
  },
  cardAmenities: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 12,
  },
  amenityChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: "#dbeafe",
    borderRadius: 8,
  },
  amenityChipText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1e40af",
  },
  cardButtons: {
    flexDirection: "row",
    gap: 8,
  },
  cardBtn: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: "#f1f5f9",
    borderRadius: 12,
    alignItems: "center",
  },
  cardBtnPrimary: {
    backgroundColor: "#3b82f6",
  },
  cardBtnText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#475569",
  },
  cardBtnTextPrimary: {
    color: "#fff",
  },

  // Skeleton for stacked cards
  skeletonCardStacked: {
    height: 120,
    borderRadius: 20,
    backgroundColor: "#e2e8f0",
    opacity: 0.5,
  },

  // Old styles (keep for other screens)
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
  tileOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 140,
    justifyContent: "space-between",
    padding: 8,
  },
  badgeRow: { flexDirection: "row", gap: 8, alignSelf: "flex-end" },
  badge: {
    backgroundColor: "rgba(17,24,39,0.72)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  badgeText: { color: "#fff", fontSize: 12, fontWeight: "800" },
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
  pill: { paddingHorizontal: 10, paddingVertical: 6, backgroundColor: "#dbeafe", borderRadius: 999 },
  pillText: { fontSize: 12, fontWeight: "700", color: "#1e40af" },
  detailImage: { width: "100%", height: 220, borderRadius: 16, marginBottom: 12 },
  detailTitle: { fontSize: 24, fontWeight: "900", marginBottom: 8 },
  primaryBtn: { backgroundColor: "#3b82f6", paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12, flex: 1 },
  primaryBtnText: { color: "#fff", fontWeight: "800", textAlign: "center" },
  secondaryBtn: { backgroundColor: "#e5e7eb", paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12, flex: 1 },
  secondaryBtnText: { color: "#111827", fontWeight: "800", textAlign: "center" },
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
  choiceChipTextActive: { color: "#1e40af" },
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
  sliderDotTextActive: { color: "#1e40af" },
  helperText: { fontSize: 12, color: "#6b7280" },
  toggleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 8 },
  toggleLabel: { fontSize: 16, fontWeight: "700" },
  toggle: { width: 54, height: 32, borderRadius: 999, backgroundColor: "#e5e7eb", padding: 4 },
  toggleOn: { backgroundColor: "#93c5fd" },
  knob: { width: 24, height: 24, borderRadius: 12, backgroundColor: "#fff" },
  knobOn: { marginLeft: 22 },
  bodyText: { fontSize: 14, color: "#111827" },
  emptyBox: {
    marginHorizontal: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#f8fafc",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "#e5e7eb",
    alignItems: "flex-start",
    gap: 4,
  },
  emptyTitle: { fontSize: 16, fontWeight: "800", color: "#111827" },
  skeletonCard: {
    height: 140,
    borderRadius: 16,
    backgroundColor: "#e5e7eb",
    opacity: 0.6,
  },
});
