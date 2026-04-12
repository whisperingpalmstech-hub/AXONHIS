/**
 * Typed API client for AXONHIS backend.
 *
 * All API calls go through this module for consistency and auth handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const API_PREFIX = "/api/v1";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${API_PREFIX}${path}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "69420",
    ...options.headers,
  };

  // Get token and locale from localStorage (client-side only)
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
    const locale = localStorage.getItem("axonhis_locale");
    if (locale) {
      (headers as Record<string, string>)["X-Locale"] = locale;
    }
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    let msg = body.detail || response.statusText;
    if (typeof msg === "object") msg = JSON.stringify(msg, null, 2);
    throw new ApiError(msg, response.status);
  }

  if (response.status === 204) return {} as T;
  return response.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { ApiError };
