/**
 * Handoff briefing view — enter a session context query and get
 * a relevance-ranked briefing of stored signals.
 */
import { useState } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "./AuthProvider";
import type { HandoffResponse, UiState } from "../types";

export const HandoffBriefing: React.FC = () => {
  const { token } = useAuth();
  const [workspace, setWorkspace] = useState("default");
  const [project, setProject] = useState("default");
  const [query, setQuery] = useState("");
  const [budgetBytes, setBudgetBytes] = useState(4000);
  const [maxSignals, setMaxSignals] = useState(15);
  const [tagsFilter, setTagsFilter] = useState("");
  const [briefing, setBriefing] = useState<HandoffResponse | null>(null);
  const [state, setState] = useState<UiState>("idle");
  const [error, setError] = useState("");

  const parseTags = (raw: string): string[] | undefined => {
    const tags = raw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    return tags.length > 0 ? tags : undefined;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !query.trim()) return;
    setState("loading");
    setError("");
    setBriefing(null);
    try {
      const resp = await api.generateHandoff(
        {
          workspace,
          project,
          query,
          budget_bytes: budgetBytes,
          max_signals: maxSignals,
          include_tags: parseTags(tagsFilter),
        },
        token,
      );
      setBriefing(resp);
      setState("idle");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to generate briefing";
      setError(msg);
      setState("error");
    }
  };

  const scorePercent = (score: number): number => {
    // Normalize score to 0-100 for display (assuming max score ~1.0)
    const normalized = Math.min(score * 50, 1.0);
    return Math.round(normalized * 100);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <h1 style={{ color: "var(--accent)" }}>Handoff Briefing</h1>
      <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
        Enter a session context query. The system uses deterministic TF-IDF +
        temporal decay to rank stored signals by relevance and returns a bounded briefing.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Workspace
            </label>
            <input
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Project
            </label>
            <input
              value={project}
              onChange={(e) => setProject(e.target.value)}
              required
            />
          </div>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Session context query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. database migration rollback in production — what should the agent know?"
            rows={4}
            required
            maxLength={10000}
            style={{ fontFamily: "inherit" }}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Budget (bytes)
            </label>
            <input
              type="number"
              value={budgetBytes}
              onChange={(e) => setBudgetBytes(Number(e.target.value))}
              min={100}
              max={50000}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Max signals
            </label>
            <input
              type="number"
              value={maxSignals}
              onChange={(e) => setMaxSignals(Number(e.target.value))}
              min={1}
              max={50}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Tag filter (optional)
            </label>
            <input
              value={tagsFilter}
              onChange={(e) => setTagsFilter(e.target.value)}
              placeholder="e.g. ops, critical"
            />
          </div>
        </div>

        {error && (
          <div style={{ color: "var(--error)", fontSize: "0.85rem" }}>{error}</div>
        )}

        <button
          type="submit"
          disabled={state === "loading" || !query.trim()}
          style={{
            background: "var(--accent)",
            color: "var(--bg)",
            fontWeight: "bold",
            cursor: state === "loading" || !query.trim() ? "default" : "pointer",
            opacity: state === "loading" || !query.trim() ? 0.5 : 1,
          }}
        >
          {state === "loading" ? "Generating…" : "Generate Briefing"}
        </button>
      </form>

      {/* Results */}
      {state === "loading" && (
        <div style={{ color: "var(--text-muted)" }}>Computing relevance scores…</div>
      )}

      {briefing && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", gap: "2rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            <span>Signals considered: {briefing.total_signals_considered}</span>
            <span>Bytes used: {briefing.budget_used} / {briefing.budget_bytes}</span>
          </div>

          {briefing.signals.length === 0 ? (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "2rem" }}>
              No matching signals found.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {briefing.signals.map((s, idx) => (
                <div
                  key={s.id}
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    padding: "1rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                    <span style={{
                      fontSize: "0.75rem",
                      color: "var(--accent)",
                      background: "rgba(0, 180, 216, 0.15)",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "4px",
                    }}>
                      #{idx + 1}
                    </span>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <div style={{ width: "4rem", height: "4rem" }}>
                        <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%" }}>
                          <circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="var(--border)"
                            strokeWidth="6"
                          />
                          <circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="var(--accent)"
                            strokeWidth="6"
                            strokeDasharray={`${scorePercent(s.relevance_score)}, 100`}
                            transform="rotate(-90 50 50)"
                          />
                        </svg>
                      </div>
                      <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                        {s.relevance_score.toFixed(2)} relevance
                      </span>
                    </div>
                  </div>

                  <p style={{ marginBottom: "0.5rem", lineHeight: 1.5 }}>{s.excerpt}</p>

                  <div style={{ display: "flex", gap: "0.5rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    <span>Tags: {s.tags.join(", ") || "none"}</span>
                    {s.agent_id && <span>Agent: {s.agent_id}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};