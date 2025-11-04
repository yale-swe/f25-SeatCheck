// seat-check/theme/ThemeProvider.tsx
import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { Appearance, ColorSchemeName } from 'react-native';
import { DarkTheme as NavDark, DefaultTheme as NavLight, Theme as NavTheme } from '@react-navigation/native';

export type ThemeMode = 'system' | 'light' | 'dark';

type StorageLike = {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
};

// Prefer AsyncStorage; fall back to in-memory so dev never crashes
let Storage: StorageLike;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const AsyncStorage = require('@react-native-async-storage/async-storage').default as StorageLike;
  Storage = AsyncStorage;
} catch {
  const mem = new Map<string, string>();
  Storage = {
    async getItem(k) { return mem.has(k) ? mem.get(k)! : null; },
    async setItem(k, v) { mem.set(k, v); },
    async removeItem(k) { mem.delete(k); },
  };
}

export type ThemeColors = {
  bg: string;
  card: string;
  text: string;
  textDim: string;
  border: string;
  primary: string;
  tabBarBg: string;
  tabBarIcon: string;
  tabBarIconActive: string;
};

const lightColors: ThemeColors = {
  bg: '#f8fafc',
  card: '#ffffff',
  text: '#0f172a',
  textDim: '#64748b',
  border: '#e2e8f0',
  primary: '#2563eb',
  tabBarBg: '#0b1324',
  tabBarIcon: '#94a3b8',
  tabBarIconActive: '#ffffff',
};

const darkColors: ThemeColors = {
  bg: '#0b1324',
  card: '#0e1a33',
  text: '#e8edf5',
  textDim: '#b9c3d6',
  border: '#1e2b48',
  primary: '#2b6cf6',
  tabBarBg: '#0b1324',
  tabBarIcon: '#8ea0b7',
  tabBarIconActive: '#ffffff',
};

export const ThemeContext = createContext<{
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  resolved: 'light' | 'dark';
  colors: ThemeColors;
  navTheme: NavTheme;
  toggleTheme: () => void;
}>({
  mode: 'system',
  setMode: () => {},
  resolved: 'light',
  colors: lightColors,
  navTheme: NavLight,
  toggleTheme: () => {},
});

const STORAGE_KEY = 'seatcheck.theme';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<ThemeMode>('system');

  const sys: ColorSchemeName = Appearance.getColorScheme();
  const resolved: 'light' | 'dark' = (mode === 'system' ? (sys || 'light') : mode) as 'light' | 'dark';
  const colors = resolved === 'dark' ? darkColors : lightColors;

  const navTheme: NavTheme = useMemo(
    () => ({
      ...(resolved === 'dark' ? NavDark : NavLight),
      colors: {
        ...(resolved === 'dark' ? NavDark.colors : NavLight.colors),
        background: colors.bg,
        card: colors.card,
        text: colors.text,
        border: colors.border,
        primary: colors.primary,
      },
    }),
    [resolved, colors]
  );

  // value setter that also persists
  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    Storage.setItem(STORAGE_KEY, m).catch(() => {});
  }, []);

  // ✅ FIX: compute next value first; don't pass a function to setMode
  const toggleTheme = useCallback(() => {
    const sysScheme = Appearance.getColorScheme() || 'light';
    const currentResolved: 'light' | 'dark' = (mode === 'system' ? sysScheme : mode) as 'light' | 'dark';
    const next: ThemeMode = currentResolved === 'dark' ? 'light' : 'dark';
    setMode(next);
  }, [mode, setMode]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const saved = await Storage.getItem(STORAGE_KEY);
        if (mounted && (saved === 'system' || saved === 'light' || saved === 'dark')) {
          setModeState(saved);
        }
      } catch {}
    })();

    const sub = Appearance.addChangeListener(() => {
      if (mode === 'system') {
        // trigger rerender on system change
        setModeState('system');
      }
    });
    return () => {
      mounted = false;
      sub.remove?.();
    };
  }, [mode]);

  const value = useMemo(
    () => ({ mode, setMode, resolved, colors, navTheme, toggleTheme }),
    [mode, setMode, resolved, colors, navTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
