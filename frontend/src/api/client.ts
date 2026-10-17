/**
 * Typed API client for the Signal Observatory backend.
 * Derived from the actual backend routes in backend/app/api/.
 */
import type {
  HandoffRequest,
  HandoffResponse,
  HealthResponse,
  LoginRequest,
  SignalCreate,
  SignalPage,
  SignalRead,
  SignalUpdate,
  TokenResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers as Record<string, string>);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const resp = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!resp.ok) {
    const text = await resp.text();
    let detail = text;
    try {
      detail = JSON.parse(text)?.detail ?? text;
    } catch {
      // keep raw text
    }
    throw new ApiError(resp.status, detail);
  }

  if (resp.status === 204) {
    return null as T;
  }

  return (await resp.json()) as T;
}

export const api = {
  // Health
  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  // Auth
  login(data: LoginRequest): Promise<TokenResponse> {
    return request<TokenResponse>("/api/auth/demo-login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  me(token: string): Promise<{ sub: string; role: string; is_admin: boolean; is_operator: boolean }> {
    return request("/api/auth/me", {}, token);
  },

  logout(token: string): Promise<{ status: string }> {
    return request<{ status: string }>("/api/auth/logout", { method: "POST" }, token);
  },

  // Signals
  createSignal(data: SignalCreate, token: string): Promise<SignalRead> {
    return request<SignalRead>("/api/signals", {
      method: "POST",
      body: JSON.stringify(data),
    }, token);
  },

  listSignals(
    params: { workspace?: string; project?: string; tags?: string[]; page?: number; per_page?: number },
    token: string,
  ): Promise<SignalPage> {
    const qs = new URLSearchParams();
    if (params.workspace) qs.append("workspace", params.workspace);
    if (params.project) qs.append("project", params.project);
    if (params.tags) params.tags.forEach((t) => qs.append("tags", t));
    if (params.page) qs.set("page", String(params.page));
    if (params.per_page) qs.set("per_page", String(params.per_page));
    const query = qs.toString();
    const url = query ? `/api/signals?${query}` : "/api/signals";
    return request<SignalPage>(url, {}, token);
  },

  getSignal(id: string, token: string): Promise<SignalRead> {
    return request<SignalRead>(`/api/signals/${id}`, {}, token);
  },

  updateSignal(id: string, data: SignalUpdate, token: string): Promise<SignalRead> {
    return request<SignalRead>(`/api/signals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }, token);
  },

  deleteSignal(id: string, token: string): Promise<void> {
    return request<void>(`/api/signals/${id}`, { method: "DELETE" }, token);
  },

  // Handoff
  generateHandoff(data: HandoffRequest, token: string): Promise<HandoffResponse> {
    return request<HandoffResponse>("/api/handoff", {
      method: "POST",
      body: JSON.stringify(data),
    }, token);
  },
};

export { ApiError };