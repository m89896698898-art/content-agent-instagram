import { apiFetch } from "./client";
import { AuthResponse, Marketplace, Period, StatsResponse, User } from "./types";

export function login(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(email: string, password: string, name: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
}

export function fetchMe(): Promise<{ user: User }> {
  return apiFetch("/auth/me");
}

export function fetchStats(period: Period, marketplace?: Marketplace): Promise<StatsResponse> {
  const query = new URLSearchParams({ period });
  if (marketplace) query.set("marketplace", marketplace);
  return apiFetch(`/stats?${query.toString()}`);
}
