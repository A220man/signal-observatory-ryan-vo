/**
 * Demo-mode login page. Users select a role and enter the role name as password.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAuth } from "./AuthProvider";
import type { UserRole } from "../types";

const roles: UserRole[] = ["viewer", "operator", "admin"];

export const LoginPage: React.FC = () => {
  const [selectedRole, setSelectedRole] = useState<UserRole>("viewer");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(selectedRole, password);
      navigate("/");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Login failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
      }}
    >
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "2.5rem",
          width: "100%",
          maxWidth: "420px",
        }}
      >
        <h1 style={{ color: "var(--accent)", marginBottom: "0.5rem" }}>
          Signal Observatory
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
          Long-term memory for agent coding CLIs. Demo mode — select a role and
          enter the role name as password.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label htmlFor="role-select" style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
              Role
            </label>
            <select
              id="role-select"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as UserRole)}
              style={{ width: "100%", padding: "0.5rem" }}
            >
              {roles.map((r) => (
                <option key={r} value={r}>
                  {r} — {r === "admin" ? "full access" : r === "operator" ? "read/write" : "read-only"}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="password-input" style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
              Password
            </label>
            <input
              id="password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter role name as password"
              style={{ width: "100%", padding: "0.5rem" }}
              required
            />
          </div>

          {error && (
            <div style={{ color: "var(--error)", fontSize: "0.85rem" }}>{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              background: "var(--accent)",
              color: "var(--bg)",
              fontWeight: "bold",
            }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
};