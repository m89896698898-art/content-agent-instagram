import AsyncStorage from "@react-native-async-storage/async-storage";

// Point this at your backend. When running the Expo dev client on a physical
// device/emulator, "localhost" won't resolve to your computer — use your
// machine's LAN IP instead (e.g. http://192.168.1.23:4000).
export const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:4000";

const TOKEN_KEY = "auth_token";

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function setToken(token: string): Promise<void> {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function clearToken(): Promise<void> {
  await AsyncStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(body.error || `Request failed with status ${res.status}`, res.status);
  }
  return body as T;
}
