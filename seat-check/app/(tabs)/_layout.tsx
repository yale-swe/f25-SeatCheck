// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { useEffect, useState } from 'react';
import { Platform } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/theme/useTheme';

const API = process.env.EXPO_PUBLIC_API_BASE ?? 'http://127.0.0.1:8000';

function AuthGate({ children }: { children: React.ReactNode }) {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('seatcheck_auth_token') : null;
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    fetch(`${API}/auth/me`, { 
      credentials: 'include',
      headers,
    })
      .then((r) => setOk(r.ok))
      .catch(() => setOk(false));
  }, []);
  useEffect(() => {
    if (ok === false) router.replace('/login');
  }, [ok]);
  if (ok === null) return null;
  return <>{children}</>;
}

export default function TabLayout() {
  const { colors, resolved } = useTheme();

  return (
    <AuthGate>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: colors.card,
            borderTopColor: colors.border,
            height: 58,
          },
          tabBarActiveTintColor: resolved === 'dark' ? '#fff' : colors.text,
          tabBarInactiveTintColor: colors.textDim,
          tabBarLabelStyle: {
            fontSize: 12,
            marginBottom: Platform.OS === 'web' ? 8 : 0,
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{ title: 'Home', tabBarIcon: ({ color, size }) => <Ionicons name="home-outline" color={color} size={size} /> }}
        />
        <Tabs.Screen
          name="explore"
          options={{ title: 'Explore', tabBarIcon: ({ color, size }) => <Ionicons name="search-outline" color={color} size={size} /> }}
        />
        <Tabs.Screen
          name="checkin"
          options={{ title: 'Check In', tabBarIcon: ({ color, size }) => <Ionicons name="checkmark-done-outline" color={color} size={size} /> }}
        />
        <Tabs.Screen
          name="map"
          options={{ title: 'Map', tabBarIcon: ({ color, size }) => <Ionicons name="map-outline" color={color} size={size} /> }}
        />
        <Tabs.Screen
          name="settings"
          options={{ title: 'Settings', tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" color={color} size={size} /> }}
        />
      </Tabs>
    </AuthGate>
  );
}
