/**
 * Dashboard — lists signals with search and pagination.
 * Shows loading, error, and empty states.
 */
import { useEffect, useState, useCallback } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "./AuthProvider";
import type { SignalPage, SignalRead, UiState } from "../types";

export const Dashboard: React.FC = () => {
  const { token, role } = useAuth();
  const [signals, setSignals] = useState<SignalRead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(50);
  const [hasMore, setHasMore] = useState(false);
  const [filterWorkspace, setFilterWorkspace] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [state, setState] = useState<UiState>("loading");
  const [error, setError] = useState("");

  const fetchSignals = useCallback(async (pageNum: number = 1) => {
    if (!token) return;
    setState("loading");
    setError("");
    try {
      const resp = await api.listSignals(
        {
          workspace: filterWorkspace || undefined,
          project: filterProject || undefined,
          page: pageNum,
          per_page: perPage,
        },
        token,
      );
      setSignals(resp.items);
      setTotal(resp.total);
      setHasMore(resp.has_more);
      setPage(resp.page);
      setState(resp.items.length === 0 ? "empty" : "loading");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to load signals";
      setError(msg);
      setState("error");
    }
  }, [token, filterWorkspace, filterProject, perPage]);

  useEffect(() => {
    fetchSignals(1);
  }, [fetchSignals]);

  const handleFilter = () => {
    fetchSignals(1);
  };

  const handleNext = () => {
    fetchSignals(page + 1);
  };

  const handlePrev = () => {
    fetchSignals(page - 1);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ color: "var(--accent)" }}>Signal Dashboard</h1>
        <span style={{ color: "var(--text-muted)", fontSize: "0.9rem", textTransform: "capitalize" }}>
          role: {role}
        </span>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Workspace
          </label>
          <input
            value={filterWorkspace}
            onChange={(e) => setFilterWorkspace(e.target.value)}
            placeholder="Filter by workspace"
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Project
          </label>
          <input
            value={filterProject}
            onChange={(e) => setFilterProject(e.target.value)}
            placeholder="Filter by project"
          />
        </div>
        <button
          onClick={handleFilter}
          style={{ background: "var(--accent)", color: "var(--bg)", fontWeight: "bold" }}
        >
          Apply Filters
        </button>
      </div>

      {/* Results */}
      {state === "loading" && (
        <div style={{ color: "var(--text-muted)" }}>Loading signals…</div>
      )}
      {state === "error" && (
        <div style={{ color: "var(--error)", padding: "1rem", background: "rgba(255,107,107,0.1)", borderRadius: "var(--radius)" }}>
          {error}
        </div>
      )}
      {state === "empty" && (
        <div style={{ color: "var(--text-muted)", padding: "2rem", textAlign: "center" }}>
          No signals found. Create one from the New Signal page.
        </div>
      )}
      {state === "loading" && signals.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)" }}>
              <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--text-muted)" }}>Workspace</th>
              <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--text-muted)" }}>Project</th>
              <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--text-muted)" }}>Content</th>
              <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--text-muted)" }}>Tags</th>
              <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--text-muted)" }}>Created</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((s) => (
              <tr key={s.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.5rem" }}>{s.workspace}</td>
                <td style={{ padding: "0.5rem" }}>{s.project}</td>
                <td style={{ padding: "0.5rem" }}>{s.content.slice(0, 80)}{s.content.length > 80 ? "…" : ""}</td>
                <td style={{ padding: "0.5rem" }}>{s.tags.join(", ")}</td>
                <td style={{ padding: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  {new Date(s.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      {total > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Showing {Math.min((page - 1) * perPage + 1, total)}–{Math.min(page * perPage, total)} of {total}
          </span>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={handlePrev}
              disabled={page <= 1}
              style={{
                background: page <= 1 ? "var(--border)" : "var(--accent)",
                color: page <= 1 ? "var(--text-muted)" : "var(--bg)",
                cursor: page <= 1 ? "default" : "pointer",
              }}
            >
              Previous
            </button>
            <button
              onClick={handleNext}
              disabled={!hasMore}
              style={{
                background: !hasMore ? "var(--border)" : "var(--accent)",
                color: !hasMore ? "var(--text-muted)" : "var(--bg)",
                cursor: !hasMore ? "default" : "pointer",
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};