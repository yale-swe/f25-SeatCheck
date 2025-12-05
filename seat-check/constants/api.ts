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

// Get auth token from localStorage (for dev auth)
export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("seatcheck_auth_token");
  }
  return null;
}

// Helper to add auth token to fetch headers
export function addAuthHeaders(headers: HeadersInit = {}): HeadersInit {
  const token = getAuthToken();
  const result: HeadersInit = { ...headers };
  if (token) {
    result["Authorization"] = `Bearer ${token}`;
  }
  return result;
}

// Convenience fetch with cookies and token
export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = addAuthHeaders({
    "Content-Type": "application/json",
    ...(init?.headers || {}),
  });

  const res = await fetch(url, {
    credentials: "include",
    headers,
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}
