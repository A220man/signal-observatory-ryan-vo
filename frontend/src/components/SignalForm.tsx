/**
 * Form for creating new memory signals.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAuth } from "./AuthProvider";

interface SignalFormData {
  workspace: string;
  project: string;
  content: string;
  tags: string;
  agent_id: string;
}

const initialState: SignalFormData = {
  workspace: "default",
  project: "default",
  content: "",
  tags: "",
  agent_id: "",
};

export const SignalForm: React.FC = () => {
  const [form, setForm] = useState<SignalFormData>(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const { token } = useAuth();
  const navigate = useNavigate();

  const handleChange = (field: keyof SignalFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const parseTags = (raw: string): string[] =>
    raw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !form.content.trim()) return;
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      await api.createSignal(
        {
          workspace: form.workspace,
          project: form.project,
          content: form.content,
          tags: parseTags(form.tags),
          agent_id: form.agent_id || undefined,
        },
        token,
      );
      setSuccess("Signal created successfully.");
      setForm(initialState);
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to create signal";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <h1 style={{ color: "var(--accent)" }}>Create New Signal</h1>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Workspace
            </label>
            <input
              value={form.workspace}
              onChange={(e) => handleChange("workspace", e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
              Project
            </label>
            <input
              value={form.project}
              onChange={(e) => handleChange("project", e.target.value)}
              required
            />
          </div>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Content (memory entry)
          </label>
          <textarea
            value={form.content}
            onChange={(e) => handleChange("content", e.target.value)}
            placeholder="Enter the signal content — what an agent should remember or be briefed on."
            rows={8}
            required
            maxLength={100000}
            style={{ fontFamily: "inherit" }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Tags (comma-separated)
          </label>
          <input
            value={form.tags}
            onChange={(e) => handleChange("tags", e.target.value)}
            placeholder="e.g. ops, critical, migration"
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem", color: "var(--text-muted)" }}>
            Agent ID (optional)
          </label>
          <input
            value={form.agent_id}
            onChange={(e) => handleChange("agent_id", e.target.value)}
            placeholder="Which agent produced this signal"
          />
        </div>

        {error && (
          <div style={{ color: "var(--error)", fontSize: "0.85rem" }}>{error}</div>
        )}
        {success && (
          <div style={{ color: "var(--success)", fontSize: "0.85rem" }}>{success}</div>
        )}

        <button
          type="submit"
          disabled={submitting || !form.content.trim()}
          style={{
            background: "var(--accent)",
            color: "var(--bg)",
            fontWeight: "bold",
            cursor: submitting || !form.content.trim() ? "default" : "pointer",
            opacity: submitting || !form.content.trim() ? 0.5 : 1,
          }}
        >
          {submitting ? "Saving…" : "Create Signal"}
        </button>
      </form>
    </div>
  );
};