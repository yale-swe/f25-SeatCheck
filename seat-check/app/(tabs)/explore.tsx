// app/(tabs)/explore.tsx
import { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Platform, TextInput } from 'react-native';
import { Image } from 'expo-image';

import { Fonts } from '@/constants/theme';
import type React from 'react';
import { useTheme } from '@/theme/useTheme';

const API = process.env.EXPO_PUBLIC_API_BASE ?? 'http://localhost:8000';
const ThemedView = View;

const webSelectStyle: React.CSSProperties = {
  width: '100%',
  height: 42,
  paddingLeft: 10,
  paddingRight: 10,
};

type Venue = {
  id: number;
  name: string;
  capacity: number;
  lat: number;
  lng: number;
  occupancy: number;
  avg_noise: number | null;
  avg_crowd: number | null;
  rating_count: number;
  photo_url?: string | null;
};

type SortKey =
  | 'popular_desc'
  | 'popular_asc'
  | 'distance'
  | 'capacity_desc'
  | 'capacity_asc'
  | 'alpha';

export default function ExploreScreen() {
  const { colors, resolved } = useTheme();
  const [venues, setVenues] = useState<Venue[]>([]);
  const [sort, setSort] = useState<SortKey>('popular_desc');
  const [userPos, setUserPos] = useState<{ lat: number; lng: number } | null>(null);
  const [query, setQuery] = useState<string>('');
  const isWeb = Platform.OS === 'web';

  // Location (fallback to Cross Campus)
  useEffect(() => {
    if (!(globalThis as any)?.navigator?.geolocation) {
      setUserPos({ lat: 41.3115, lng: -72.926 });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setUserPos({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setUserPos({ lat: 41.3115, lng: -72.926 })
    );
  }, []);

  // Fetch venues
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/api/v1/venues`, { credentials: 'include' });
        if (!r.ok) return;
        const data = await r.json();
        const mapped: Venue[] = data.map((v: any) => ({
          id: v.id,
          name: v.name,
          capacity: v.capacity ?? 0,
          lat: v.lat ?? 0,
          lng: v.lon ?? 0,                 // <-- backend uses `lon`
          occupancy: v.occupancy ?? 0,
          avg_noise: v.avg_noise ?? null,
          avg_crowd: v.avg_occupancy ?? null,
          rating_count: v.rating_count ?? 0,
          photo_url: v.image_url ?? null,  // <-- read `image_url` from API
        }));
        setVenues(mapped);
      } catch {
        /* ignore */
      }
    })();
  }, []);


  // Distances
  const withDistance = useMemo(() => {
    if (!userPos) return venues.map((v) => ({ ...v, distanceKm: null as number | null }));
    return venues.map((v) => ({
      ...v,
      distanceKm: haversine(userPos.lat, userPos.lng, v.lat, v.lng),
    }));
  }, [venues, userPos]);

  // Filter (search)
  const filtered = useMemo<(Venue & { distanceKm?: number | null })[]>(() => {
    const q = query.trim().toLowerCase();
    if (!q) return withDistance;
    return withDistance.filter((v) => v.name.toLowerCase().includes(q));
  }, [withDistance, query]);

  // Sort
  const sorted: (Venue & { distanceKm?: number | null })[] = useMemo(() => {
    const arr = [...filtered];
    switch (sort) {
      case 'popular_desc':
        arr.sort((a, b) => (b.rating_count ?? 0) - (a.rating_count ?? 0));
        break;
      case 'popular_asc':
        arr.sort((a, b) => (a.rating_count ?? 0) - (b.rating_count ?? 0));
        break;
      case 'distance':
        arr.sort((a, b) => (a.distanceKm ?? 1e9) - (b.distanceKm ?? 1e9));
        break;
      case 'capacity_desc':
        arr.sort((a, b) => (b.capacity ?? 0) - (a.capacity ?? 0));
        break;
      case 'capacity_asc':
        arr.sort((a, b) => (a.capacity ?? 0) - (b.capacity ?? 0));
        break;
      case 'alpha':
        arr.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }
    return arr;
  }, [filtered, sort]);

  // Theme-aware status colors for the occupancy bar
  const status = {
    ok: resolved === 'dark' ? '#30a46c' : '#15803d',
    warn: resolved === 'dark' ? '#f5a623' : '#b45309',
    danger: resolved === 'dark' ? '#e4572e' : '#b91c1c',
  };

  return (
    <ThemedView style={[s.page, { backgroundColor: colors.bg }]}>
      <View style={s.header}>
        <Text style={[s.sectionTitle, { color: colors.text }]}>
          Explore
        </Text>
      </View>

      {/* Search */}
      <View style={s.searchRow}>
        <TextInput
          placeholder="Search study spots…"
          placeholderTextColor={colors.textDim}
          value={query}
          onChangeText={setQuery}
          style={[
            s.search,
            { backgroundColor: colors.card, color: colors.text, borderColor: colors.border },
          ]}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {query.length > 0 && (
          <Pressable
            onPress={() => setQuery('')}
            style={[s.clearBtn, { backgroundColor: colors.card, borderColor: colors.border }]}
          >
            <Text style={[s.clearBtnText, { color: colors.text }]}>Clear</Text>
          </Pressable>
        )}
      </View>

      {/* Sort */}
      <View style={s.sortRow}>
        <Text style={[s.sortLabel, { color: colors.textDim }]}>Sort by</Text>

        {isWeb ? (
          <div style={{ flex: 1 }}>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              style={{
                ...webSelectStyle,
                backgroundColor: colors.card,
                color: colors.text,
                border: '1px solid ' + colors.border,
                borderRadius: 10,
                outline: 'none',
                appearance: 'none',
              }}
            >
              <option value="popular_desc">Most → least popular</option>
              <option value="popular_asc">Least → most popular</option>
              <option value="distance">Distance from you</option>
              <option value="capacity_desc">Most → least capacity</option>
              <option value="capacity_asc">Least → most capacity</option>
              <option value="alpha">Alphabetical</option>
            </select>
          </div>
        ) : (
          <View style={s.fallbackPills}>
            {([
              ['popular_desc', 'Popular ↓'],
              ['popular_asc', 'Popular ↑'],
              ['distance', 'Distance'],
              ['capacity_desc', 'Capacity ↓'],
              ['capacity_asc', 'Capacity ↑'],
              ['alpha', 'A–Z'],
            ] as [SortKey, string][]).map(([key, label]) => {
              const active = sort === key;
              return (
                <Pressable
                  key={key}
                  onPress={() => setSort(key)}
                  style={[
                    s.pill,
                    { backgroundColor: colors.card, borderColor: colors.border },
                    active && { backgroundColor: colors.primary, borderColor: colors.primary },
                  ]}
                >
                  <Text
                    style={[
                      s.pillText,
                      { color: colors.text },
                      active && { color: '#fff', fontWeight: '700' },
                    ]}
                  >
                    {label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        )}
      </View>

      {/* List */}
      <ScrollView contentContainerStyle={[s.list, { paddingBottom: 80 }]}>
        {sorted.length === 0 ? (
          <View style={[s.emptyBox, { backgroundColor: colors.card, borderColor: colors.border }]}>
            <Text style={[s.emptyTitle, { color: colors.text }]}>No matching spots</Text>
            <Text style={[s.helperText, { color: colors.textDim }]}>Try another name</Text>
          </View>
        ) : (
          sorted.map((v) => (
            <VenueCard key={v.id} v={v} colors={colors} status={status} />
          ))
        )}
      </ScrollView>
    </ThemedView>
  );
}

function VenueCard({
  v,
  colors,
  status,
}: {
  v: Venue & { distanceKm?: number | null };
  colors: ReturnType<typeof useTheme>['colors'];
  status: { ok: string; warn: string; danger: string };
}) {
  const ratio = v.capacity ? Math.min(100, Math.round((v.occupancy / v.capacity) * 100)) : 0;
  const color = ratio <= 25 ? status.ok : ratio <= 70 ? status.warn : status.danger;
  const barW = Math.max(6, Math.min(100, ratio));

  return (
    <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <Image source={v.photo_url || placeholderFor(v.name)} style={s.cardImg} contentFit="cover" />
      <View style={s.cardBody}>
        <Text style={[s.cardTitle, { color: colors.text }]}>{v.name}</Text>
        <Text style={[s.meta, { color: colors.text }]}>
          {v.capacity ? `${v.occupancy}/${v.capacity} • ${ratio}%` : `${v.occupancy} checked in`}
          {typeof v.distanceKm === 'number' ? ` • ${v.distanceKm.toFixed(1)} km` : ''}
        </Text>
        <Text style={[s.metaDim, { color: colors.textDim }]}>
          Noise avg: {v.avg_noise ?? '—'} • Crowd avg: {v.avg_crowd ?? '—'} • Ratings: {v.rating_count}
        </Text>

        <View style={[s.barTrack, { backgroundColor: colors.bg }]}>
          <View style={[s.barFill, { width: `${barW}%`, backgroundColor: color }]} />
        </View>

        <View style={s.cardActions}>
          <Pressable onPress={() => checkIn(v.id)} style={[s.btnPrimary, { backgroundColor: colors.primary }]}>
            <Text style={s.btnPrimaryText}>Check in</Text>
          </Pressable>
          <Pressable
            onPress={() => checkOut(v.id)}
            style={[s.btn, { backgroundColor: colors.card, borderColor: colors.border }]}
          >
            <Text style={[s.btnText, { color: colors.text }]}>Check out</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

/* helpers */

async function checkIn(venue_id: number) {
  await fetch(`${API}/checkins`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ venue_id }),
  });
}

async function checkOut(venue_id: number) {
  await fetch(`${API}/checkins/checkout`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ venue_id }),
  });
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number) {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Neutral placeholder if no photo_url
function placeholderFor(name: string) {
  const label = encodeURIComponent(name);
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360'>
    <defs>
      <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
        <stop offset='0%' stop-color='#0e1a33'/>
        <stop offset='100%' stop-color='#112142'/>
      </linearGradient>
    </defs>
    <rect width='100%' height='100%' fill='url(#g)'/>
    <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle'
      fill='#e8edf5' font-size='28' font-family='sans-serif'>${label}</text>
  </svg>`;
  return `data:image/svg+xml;utf8,${svg}`;
}

/* styles */

const s = StyleSheet.create({
  page: { flex: 1, padding: 16 },
  header: { marginBottom: 6 }, // match spacing vibe from check-in
  sectionTitle: { fontSize: 18, fontWeight: '800', marginBottom: 6 },

  searchRow: { flexDirection: 'row', gap: 8, alignItems: 'center', marginBottom: 10 },
  search: { flex: 1, height: 42, paddingHorizontal: 12, borderWidth: 1, borderRadius: 10 },
  clearBtn: {
    paddingHorizontal: 10,
    height: 42,
    borderWidth: 1,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  clearBtnText: { fontWeight: '700' },
  sortRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  sortLabel: {},
  fallbackPills: { flex: 1, flexWrap: 'wrap', flexDirection: 'row', gap: 8 },
  pill: { borderWidth: 1, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8 },
  pillText: { fontSize: 12 },
  list: { gap: 12 },
  card: { borderWidth: 1, borderRadius: 14, overflow: 'hidden' },
  cardImg: { width: '100%', height: 160 },
  cardBody: { padding: 12, gap: 6 },
  cardTitle: { fontWeight: '700', fontSize: 16 },
  meta: {},
  metaDim: { fontSize: 12 },
  barTrack: { height: 8, borderRadius: 6, overflow: 'hidden', marginTop: 6 },
  barFill: { height: 8 },
  cardActions: { flexDirection: 'row', gap: 8, marginTop: 10 },
  btnPrimary: { borderRadius: 10, paddingVertical: 8, paddingHorizontal: 12 },
  btnPrimaryText: { color: '#fff', fontWeight: '700' },
  btn: { borderWidth: 1, borderRadius: 10, paddingVertical: 8, paddingHorizontal: 12 },
  btnText: {},
  emptyBox: { padding: 16, borderRadius: 12, borderWidth: 1, alignItems: 'flex-start', gap: 4 },
  emptyTitle: { fontSize: 16, fontWeight: '800' },
  helperText: { fontSize: 12 },
});
