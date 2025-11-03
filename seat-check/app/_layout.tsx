// app/_layout.tsx
import React from 'react';
import { ThemeProvider as NavThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';

import { ThemeProvider } from '../theme/ThemeProvider';
import { useTheme } from '../theme/useTheme';

function Inner() {
  const { navTheme, resolved, colors } = useTheme();

  return (
    <NavThemeProvider value={navTheme}>
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="login"
          options={{
            headerShown: true,
            title: 'Login',
            headerStyle: { backgroundColor: colors.card },
            headerTintColor: colors.text,
          }}
        />
      </Stack>
      <StatusBar style={resolved === 'dark' ? 'light' : 'dark'} backgroundColor={colors.bg} />
    </NavThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <Inner />
    </ThemeProvider>
  );
}
