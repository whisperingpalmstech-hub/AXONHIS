// Shared API utilities for AxonHIS MD
export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function apiFetch<T = any>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}/api/v1/md${path}`, {
    ...opts,
    headers: { ...authHeaders(), ...(opts?.headers || {}) },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function apiPost<T = any>(path: string, body: any): Promise<T> {
  return apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export async function apiPut<T = any>(path: string, body: any): Promise<T> {
  return apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export async function apiDelete(path: string): Promise<any> {
  return apiFetch(path, { method: "DELETE" });
}
