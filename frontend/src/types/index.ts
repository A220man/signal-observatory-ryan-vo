/**
 * Type definitions for the Signal Observatory frontend.
 * Derived from the backend API schema (backend/app/models/schemas.py).
 */

export type UserRole = "viewer" | "operator" | "admin";

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  role: UserRole;
}

export interface LoginRequest {
  role: UserRole;
  password: string;
}

export interface SignalBase {
  workspace: string;
  project: string;
  content: string;
  tags: string[];
  agent_id?: string | null;
}

export interface SignalRead extends SignalBase {
  id: string;
  created_at: string;
  updated_at: string;
  relevance_score: number;
}

export interface SignalCreate extends SignalBase {}

export interface SignalUpdate {
  content?: string;
  tags?: string[];
  agent_id?: string | null;
}

export interface SignalPage {
  items: SignalRead[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface HandoffRequest {
  workspace: string;
  project: string;
  query: string;
  budget_bytes?: number;
  max_signals?: number;
  include_tags?: string[] | null;
  decay_half_life_days?: number | null;
}

export interface HandoffSignal {
  id: string;
  relevance_score: number;
  excerpt: string;
  tags: string[];
  agent_id?: string | null;
  created_at: string;
}

export interface HandoffResponse {
  workspace: string;
  project: string;
  query: string;
  total_signals_considered: number;
  budget_bytes: number;
  budget_used: number;
  signals: HandoffSignal[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

// UI state for auth
export interface AuthContextType {
  token: string | null;
  role: UserRole | null;
  login: (role: UserRole, password: string) => Promise<void>;
  logout: () => void;
}

// Loading / error state
export type UiState = "idle" | "loading" | "error" | "empty";