// app/(tabs)/index.tsx
import { useEffect, useState } from 'react';
import { View, Text, Pressable, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import { Link, useRouter } from 'expo-router';
import { useTheme } from '@/theme/useTheme';

const API = process.env.EXPO_PUBLIC_API_BASE ?? 'http://localhost:8000';
const isWeb = Platform.OS === 'web';

type Me = { netid: string } | null;

export default function HomeScreen() {
  const router = useRouter();
  const { colors } = useTheme();

  const [me, setMe] = useState<Me>(null);
  const [loading, setLoading] = useState(true);

  // Check session once on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('seatcheck_auth_token') : null;
        const headers: HeadersInit = { 'Content-Type': 'application/json' };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        const r = await fetch(`${API}/auth/me`, {
          credentials: 'include',
          headers,
        });
        const data = r.ok ? await r.json() : null;
        if (!cancelled) setMe(data);
      } catch {
        if (!cancelled) setMe(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Redirect to /login only when confirmed NOT logged in
  useEffect(() => {
    if (!loading && !me) {
      router.replace('/login');
    }
  }, [loading, me, router]);

  if (loading) {
    return (
      <View style={[s.page, s.center, { backgroundColor: colors.bg }]}>
        <ActivityIndicator color={colors.text} />
        <Text style={[s.dim, { color: colors.textDim }]}>Checking session…</Text>
      </View>
    );
  }

  if (me) {
    return (
      <View style={[s.page, { backgroundColor: colors.bg }]}>
        <View style={s.topRow}>
          {isWeb ? (
            <Link href="/login" style={{ textDecorationLine: 'none' }}>
              <Pressable style={[s.loginBtn, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.loginText, { color: colors.text }]}>Go to Login</Text>
              </Pressable>
            </Link>
          ) : (
            <Link href="/login" asChild>
              <Pressable style={[s.loginBtn, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.loginText, { color: colors.text }]}>Go to Login</Text>
              </Pressable>
            </Link>
          )}
          <Text style={[s.netid, { color: colors.textDim }]}>Logged in as {me.netid}</Text>
        </View>

        <Text style={[s.h1, { color: colors.text }]}>SeatCheck</Text>
        <Text style={[s.p, { color: colors.textDim }]}>
          Find the best Yale study spots with live occupancy and ratings.
        </Text>

        <View style={s.ctaRow}>
          {isWeb ? (
            <Link href="/(tabs)/map" style={{ textDecorationLine: 'none' }}>
              <Pressable style={[s.primary, { backgroundColor: colors.primary }]}>
                <Text style={s.primaryText}>Open Map</Text>
              </Pressable>
            </Link>
          ) : (
            <Link href="/(tabs)/map" asChild>
              <Pressable style={[s.primary, { backgroundColor: colors.primary }]}>
                <Text style={s.primaryText}>Open Map</Text>
              </Pressable>
            </Link>
          )}

          {isWeb ? (
            <Link href="/(tabs)/explore" style={{ textDecorationLine: 'none' }}>
              <Pressable style={[s.secondary, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.secondaryText, { color: colors.text }]}>Explore List</Text>
              </Pressable>
            </Link>
          ) : (
            <Link href="/(tabs)/explore" asChild>
              <Pressable style={[s.secondary, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.secondaryText, { color: colors.text }]}>Explore List</Text>
              </Pressable>
            </Link>
          )}
        </View>
      </View>
    );
  }

  return null;
}

const s = StyleSheet.create({
  page: { flex: 1, padding: 24, gap: 16 },
  center: { alignItems: 'center', justifyContent: 'center' },

  topRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  loginBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  loginText: { fontWeight: '600' },
  netid: {},

  h1: { fontSize: 28, fontWeight: '700', marginTop: 8 },
  p: { fontSize: 15, lineHeight: 22 },

  ctaRow: { flexDirection: 'row', gap: 12, marginTop: 6 },
  primary: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10 },
  primaryText: { color: '#fff', fontWeight: '700' },
  secondary: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10, borderWidth: 1 },
  secondaryText: { fontWeight: '600' },

  dim: { marginTop: 8 },
});
