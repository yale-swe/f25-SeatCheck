// app/(tabs)/checkin.tsx
import { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Pressable,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '@/theme/useTheme';
import { API, fetchJSON } from '@/constants/api';

type NoiseLevel = 'silent' | 'quiet' | 'moderate' | 'loud';
const noiseMap: Record<NoiseLevel, number> = { silent: 0, quiet: 2, moderate: 3, loud: 5 };

type Venue = {
  id: number;
  name: string;
  lat: number;
  lon: number; // backend uses 'lon'
  capacity: number | null;
  occupancy: number | null; // live presence (active check-ins)
};

export default function CheckInScreen() {
  const { colors } = useTheme();

  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [occupancy, setOccupancy] = useState<number>(3);
  const [noise, setNoise] = useState<NoiseLevel>('moderate');
  const [busy, setBusy] = useState(false);

  const loadVenues = useCallback(async () => {
    try {
      const raw = await fetchJSON<any[]>(API.venues);
      const mapped: Venue[] = raw.map((v) => ({
        id: Number(v.id),
        name: String(v.name),
        lat: Number(v.lat ?? 0),
        lon: Number(v.lon ?? 0),
        capacity: v.capacity != null ? Number(v.capacity) : null,
        occupancy: v.occupancy != null ? Number(v.occupancy) : null,
      }));
      setVenues(mapped);
      if (mapped.length && selectedId == null) setSelectedId(mapped[0].id);
    } catch (e: any) {
      Alert.alert('Failed to load venues', String(e?.message || e));
      setVenues([]);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadVenues();
  }, [loadVenues]);

  const submit = async () => {
    if (!selectedId) {
      return Alert.alert('Pick a location', 'Please choose where you are.');
    }
    try {
      setBusy(true);

      // 1) Presence check-in (updates live occupancy)
      {
        const r = await fetch(API.checkins, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ venue_id: selectedId }),
        });
        if (!r.ok) {
          const t = await r.text();
          throw new Error(`Presence check-in failed: ${r.status} ${r.statusText}\n${t}`);
        }
      }

      // 2) Rating submit (updates averages)
      {
        const r2 = await fetch(API.ratings, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            venue_id: selectedId,
            occupancy,              // 0–5 scale for perceived crowding
            noise: noiseMap[noise], // 0–5 scale
          }),
        });
        if (!r2.ok) {
          const t = await r2.text();
          throw new Error(`Rating submit failed: ${r2.status} ${r2.statusText}\n${t}`);
        }
      }

      // 3) Refresh local list so UI reflects new values
      await loadVenues();
      Alert.alert('Thanks!', 'Your check-in and rating were submitted.');
    } catch (e: any) {
      Alert.alert('Submit failed', String(e?.message || e));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <View style={[s.page, s.center, { backgroundColor: colors.bg }]}>
        <ActivityIndicator color={colors.text} />
        <Text style={[s.dim, { color: colors.textDim }]}>Loading venues…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={[s.page, { backgroundColor: colors.bg }]} contentContainerStyle={{ padding: 16, gap: 16 }}>
      {/* Location */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Location</Text>
        <View style={[s.selectBox, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <Text style={[s.selectLabel, { color: colors.textDim }]}>Choose a place</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            {venues.map((v) => {
              const active = v.id === selectedId;
              return (
                <TouchableOpacity
                  key={v.id}
                  style={[
                    s.choiceChip,
                    { backgroundColor: colors.card, borderColor: colors.border },
                    active && { backgroundColor: colors.primary, borderColor: colors.primary },
                  ]}
                  onPress={() => setSelectedId(v.id)}
                  activeOpacity={0.9}
                >
                  <Text
                    style={[
                      s.choiceChipText,
                      { color: colors.text },
                      active && { color: '#fff' },
                    ]}
                  >
                    {v.name}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      </View>

      {/* Occupancy */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Occupancy (0–5)</Text>
        <View style={s.sliderRow}>
          {[0, 1, 2, 3, 4, 5].map((n) => {
            const active = occupancy === n;
            return (
              <Pressable
                key={n}
                onPress={() => setOccupancy(n)}
                style={[
                  s.sliderDot,
                  { backgroundColor: colors.card, borderColor: colors.border },
                  active && { backgroundColor: colors.primary, borderColor: colors.primary },
                ]}
              >
                <Text
                  style={[
                    s.sliderDotText,
                    { color: colors.text },
                    active && { color: '#fff' },
                  ]}
                >
                  {n}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <Text style={[s.helperText, { color: colors.textDim }]}>
          0 empty · 1 very light · 2 light · 3 moderate · 4 crowded · 5 packed
        </Text>
      </View>

      {/* Noise */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Noise</Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
          {(['silent', 'quiet', 'moderate', 'loud'] as NoiseLevel[]).map((lvl) => {
            const active = noise === lvl;
            return (
              <Pressable
                key={lvl}
                onPress={() => setNoise(lvl)}
                style={[
                  s.choiceChip,
                  { backgroundColor: colors.card, borderColor: colors.border },
                  active && { backgroundColor: colors.primary, borderColor: colors.primary },
                ]}
              >
                <Text
                  style={[
                    s.choiceChipText,
                    { color: colors.text },
                    active && { color: '#fff' },
                  ]}
                >
                  {lvl}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Submit */}
      <Pressable
        style={[s.primaryBtn, { backgroundColor: colors.primary }, busy && { opacity: 0.6 }]}
        disabled={busy}
        onPress={submit}
      >
        <Text style={s.primaryBtnText}>{busy ? 'Submitting…' : 'Submit check-in'}</Text>
      </Pressable>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { flex: 1 },
  center: { alignItems: 'center', justifyContent: 'center' },
  dim: { marginTop: 8 },

  sectionTitle: { fontSize: 18, fontWeight: '800', marginBottom: 6 },

  selectBox: {
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  selectLabel: { fontSize: 14, marginBottom: 8 },

  choiceChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
  },
  choiceChipText: { fontWeight: '700' },

  sliderRow: { flexDirection: 'row', gap: 8 },
  sliderDot: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
  },
  sliderDotText: { fontWeight: '800' },

  helperText: { fontSize: 12, marginTop: 6 },

  primaryBtn: { paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12 },
  primaryBtnText: { color: '#fff', fontWeight: '800', textAlign: 'center' },
});
