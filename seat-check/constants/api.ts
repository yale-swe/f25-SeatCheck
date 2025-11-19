// seat-check/constants/api.ts
// Optionally set EXPO_PUBLIC_API_BASE in .env (e.g., http://192.168.1.10:8000)
// If unset, relative paths are used so cookies work in dev.

const BASE = process.env.EXPO_PUBLIC_API_BASE?.replace(/\/+$/, "") || "";

export const API_PREFIX = `${BASE}/api/v1`;

export const API = {
  // non-versioned
  health: `${BASE}/health`,
  authMe: `${BASE}/auth/me`,
  devLogin: `${BASE}/auth/dev/login`,

  // v1
  venues: `${API_PREFIX}/venues`,
  venuesGeoJSON: `${API_PREFIX}/venues/.geojson`,
  checkins: `${API_PREFIX}/checkins`,
  heartbeat: `${API_PREFIX}/checkins/heartbeat`,
  checkout: `${API_PREFIX}/checkins/checkout`,
  ratings: `${API_PREFIX}/ratings`,
};

// Convenience fetch with cookies
export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}
