import { vi } from 'vitest'

// Mock react-native FIRST before any other imports
vi.mock('react-native', () => ({
  useColorScheme: () => 'light',
  Appearance: {
    getColorScheme: () => 'light',
    addChangeListener: () => ({ remove: () => {} }),
  },
  Platform: {
    select: (obj) => obj.default ?? obj.web,
    OS: 'web',
  },
}))

// Mock AsyncStorage used by ThemeProvider fallback
vi.mock('@react-native-async-storage/async-storage', () => ({
  default: {
    getItem: vi.fn(() => Promise.resolve(null)),
    setItem: vi.fn(() => Promise.resolve()),
    removeItem: vi.fn(() => Promise.resolve()),
  },
}))

// Mock expo-constants if referenced by code/tests
vi.mock('expo-constants', () => ({
  default: {
    expoConfig: {},
    manifest: {},
  },
}))

// Mock @react-navigation/native
vi.mock('@react-navigation/native', () => ({
  DarkTheme: {
    dark: true,
    colors: {
      primary: '#fff',
      background: '#000',
      card: '#222',
      text: '#fff',
      border: '#333',
      notification: '#ff0000',
    },
  },
  DefaultTheme: {
    dark: false,
    colors: {
      primary: '#000',
      background: '#fff',
      card: '#f0f0f0',
      text: '#000',
      border: '#ccc',
      notification: '#ff0000',
    },
  },
}))
