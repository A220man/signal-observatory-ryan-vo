/**
 * Signal Detail View — view and edit individual memory signals.
 * Completes the CRUD workflow: create (SignalForm), list (Dashboard), read/update (SignalDetail), delete (Dashboard).
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAuth } from "./AuthProvider";
import type { SignalRead, SignalUpdate, UserRole } from "../types";

export const SignalDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { token, role } = useAuth();
  const navigate = useNavigate();

  const [signal, setSignal] = useState<SignalRead | null>(null);
  const [state, setState] = useState<"loading" | "error" | "ready">("loading");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<SignalUpdate>({ content: "", tags: [], agent_id: null });
  const [submitting, setSubmitting] = useState(false);

  const isOperator = role === "operator" || role === "admin";

  useEffect(() => {
    if (!token || !id) return;
    setState("loading");
    setError("");
    api
      .getSignal(id, token)
      .then((s) => {
        setSignal(s);
        setForm({ content: s.content, tags: s.tags, agent_id: s.agent_id });
        setState("ready");
      })
      .catch((err) => {
        const msg = err instanceof ApiError ? err.message : "Failed to load signal";
        setError(msg);
        setState("error");
      });
  }, [token, id]);

  const handleChange = (field: keyof SignalUpdate, value: string | string[] | null) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const parseTags = (raw: string): string[] =>
    raw.split(",").map((t) => t.trim()).filter(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !id) return;
    setSubmitting(true);
    setError("");
    try {
      const payload: SignalUpdate = {
        content: form.content || undefined,
        tags: form.tags && form.tags.length > 0 ? form.tags : undefined,
        agent_id: form.agent_id || undefined,
      };
      const updated = await api.updateSignal(id, payload, token);
      setSignal(updated);
      setForm({ content: updated.content, tags: updated.tags, agent_id: updated.agent_id });
      setEditing(false);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Update failed";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!token || !id) return;
    if (!confirm("Delete this signal? This cannot be undone.")) return;
    try {
      await api.deleteSignal(id, token);
      navigate("/");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Delete failed";
      setError(msg);
    }
  };

  const formatDate = (iso: string) => new Date(iso).toLocaleString();

  const tagStyles = {
    display: "inline-block",
    background: "var(--accent-muted)",
    color: "var(--accent)",
    padding: "0.15rem 0.5rem",
    borderRadius: "0.25rem",
    fontSize: "0.8rem",
    marginRight: "0.35rem",
    marginBottom: "0.35rem",
  } as const;

  if (state === "loading") {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
        Loading signal…
      </div>
    );
  }

  if (state === "error" || !signal) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error || "Signal not found"}</p>
        <Link to="/" style={{ color: "var(--accent)" }}>
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <Link to="/" style={{ color: "var(--accent)", textDecoration: "none", marginRight: "1rem" }}>
            ← Dashboard
          </Link>
          <h1 style={{ margin: 0, fontSize: "1.5rem" }}>Signal {signal.id.slice(0, 8)}…</h1>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {isOperator && !editing && (
            <button onClick={() => setEditing(true)} style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "0.5rem 1rem" }}>
              Edit
            </button>
          )}
          {role === "admin" && !editing && (
            <button onClick={handleDelete} style={{ background: "var(--danger)", border: "none", color: "white", padding: "0.5rem 1rem" }}>
              Delete
            </button>
          )}
          {editing && (
            <>
              <button onClick={() => { setForm({ content: signal.content, tags: signal.tags, agent_id: signal.agent_id }); setEditing(false); }} style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "0.5rem 1rem" }}>
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "0.5rem", padding: "1rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", fontSize: "0.9rem" }}>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Workspace:</strong>
            <span style={{ marginLeft: "0.5rem" }}>{signal.workspace}</span>
          </div>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Project:</strong>
            <span style={{ marginLeft: "0.5rem" }}>{signal.project}</span>
          </div>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Agent:</strong>
            <span style={{ marginLeft: "0.5rem" }}>{signal.agent_id || "—"}</span>
          </div>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Created:</strong>
            <span style={{ marginLeft: "0.5rem" }}>{formatDate(signal.created_at)}</span>
          </div>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Updated:</strong>
            <span style={{ marginLeft: "0.5rem" }}>{formatDate(signal.updated_at)}</span>
          </div>
          <div>
            <strong style={{ color: "var(--text-muted)" }}>Relevance Score:</strong>
            <span style={{ marginLeft: "0.5rem", fontFamily: "monospace" }}>{signal.relevance_score.toFixed(4)}</span>
          </div>
        </div>

        {/* Tags */}
        <div style={{ marginTop: "1rem" }}>
          <strong style={{ color: "var(--text-muted)" }}>Tags:</strong>
          <div style={{ marginTop: "0.5rem" }}>
            {signal.tags.length > 0 ? (
              signal.tags.map((t, i) => <span key={i} style={tagStyles}>{t}</span>)
            ) : (
              <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No tags</span>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "0.5rem", padding: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <strong>Content</strong>
          {editing && (
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Markdown supported</span>
          )}
        </div>

        {editing ? (
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <textarea
              value={form.content}
              onChange={(e) => handleChange("content", e.target.value)}
              style={{
                minHeight: "200px",
                padding: "0.75rem",
                border: "1px solid var(--border)",
                borderRadius: "0.375rem",
                background: "var(--bg)",
                color: "var(--text)",
                fontFamily: "monospace",
                fontSize: "0.9rem",
                resize: "vertical",
              }}
              required
            />
            <div>
              <label style={{ display: "block", marginBottom: "0.35rem", fontSize: "0.9rem" }}>
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={form.tags?.join(", ") || ""}
                onChange={(e) => handleChange("tags", parseTags(e.target.value))}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid var(--border)",
                  borderRadius: "0.375rem",
                  background: "var(--bg)",
                  color: "var(--text)",
                }}
                placeholder="bug, fix, auth, memory"
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: "0.35rem", fontSize: "0.9rem" }}>
                Agent ID
              </label>
              <input
                type="text"
                value={form.agent_id || ""}
                onChange={(e) => handleChange("agent_id", e.target.value || null)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid var(--border)",
                  borderRadius: "0.375rem",
                  background: "var(--bg)",
                  color: "var(--text)",
                }}
                placeholder="claude-code, open-code, etc."
              />
            </div>
            {error && <p style={{ color: "var(--danger)", margin: 0 }}>{error}</p>}
            <button
              type="submit"
              disabled={submitting || !(form.content?.trim())}
              style={{
                background: "var(--accent)",
                border: "none",
                color: "white",
                padding: "0.6rem 1.25rem",
                borderRadius: "0.375rem",
                cursor: submitting || !(form.content?.trim()) ? "not-allowed" : "pointer",
                opacity: submitting || !(form.content?.trim()) ? 0.6 : 1,
              }}
            >
              {submitting ? "Saving…" : "Save Changes"}
            </button>
          </form>
        ) : (
          <div
            style={{
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              fontFamily: "monospace",
              fontSize: "0.9rem",
              lineHeight: "1.6",
            }}
          >
            {signal.content}
          </div>
        )}
      </div>
    </div>
  );
};