/**
 * Frontend tests covering user-visible behavior.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { AuthContext } from "./components/AuthProvider";
import { Dashboard } from "./components/Dashboard";
import { LoginPage } from "./components/LoginPage";
import { SignalDetail } from "./components/SignalDetail";
import * as apiModule from "./api/client";
import { ApiError } from "./api/client";
import type { AuthContextType, UserRole, SignalPage, SignalRead } from "./types";

// Mock the API client
vi.mock("./api/client", () => ({
  api: {
    health: vi.fn().mockResolvedValue({ status: "ok", service: "signal-observatory", version: "1.0.0" }),
    login: vi.fn(),
    me: vi.fn(),
    logout: vi.fn(),
    createSignal: vi.fn(),
    listSignals: vi.fn(),
    getSignal: vi.fn(),
    updateSignal: vi.fn(),
    deleteSignal: vi.fn(),
    generateHandoff: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(public status: number, message: string) {
      super(message);
    }
  },
}));

const makeContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => ({
  token: null,
  role: null,
  login: vi.fn(),
  logout: vi.fn(),
  ...overrides,
});

const renderWithAuth = (
  ui: React.ReactElement,
  context: AuthContextType,
  initialRoute = "/",
) =>
  render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <AuthContext.Provider value={context}>{ui}</AuthContext.Provider>
    </MemoryRouter>,
  );

const emptyPage: SignalPage = {
  items: [],
  total: 0,
  page: 1,
  per_page: 50,
  has_more: false,
};

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders role selector and password field", () => {
    renderWithAuth(<LoginPage />, makeContext());
    expect(screen.getByLabelText("Role")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  it("calls login with correct credentials on submit", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    renderWithAuth(<LoginPage />, makeContext({ login }));

    const passwordInput = screen.getByLabelText("Password");
    fireEvent.change(passwordInput, { target: { value: "viewer" } });

    fireEvent.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("viewer", "viewer");
    });
  });

  it("shows error message on failed login", async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401, "Invalid credentials"));
    renderWithAuth(<LoginPage />, makeContext({ login }));

    const passwordInput = screen.getByLabelText("Password");
    fireEvent.change(passwordInput, { target: { value: "wrong" } });

    fireEvent.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially then empty state for no signals", async () => {
    vi.mocked(apiModule.api.listSignals).mockResolvedValue(emptyPage);

    renderWithAuth(<Dashboard />, makeContext({ token: "test", role: "viewer" }));

    expect(screen.getByText(/Signal Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/loading signals/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/no signals found/i)).toBeInTheDocument();
    });
  });

  it("displays signals in a table when data is loaded", async () => {
    const pageWithData: SignalPage = {
      items: [
        {
          id: "sig-1",
          workspace: "proj-ws",
          project: "my-project",
          content: "This is a test signal about database migration",
          tags: ["ops", "critical"],
          agent_id: "agent-a",
          created_at: "2024-01-15T10:30:00Z",
          updated_at: "2024-01-15T10:30:00Z",
          relevance_score: 0.0,
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
      has_more: false,
    };
    vi.mocked(apiModule.api.listSignals).mockResolvedValue(pageWithData);

    renderWithAuth(<Dashboard />, makeContext({ token: "test", role: "viewer" }));

    await waitFor(() => {
      expect(screen.getByText("proj-ws")).toBeInTheDocument();
    });

    expect(screen.getByText("my-project")).toBeInTheDocument();
    expect(screen.getByText(/database migration/i)).toBeInTheDocument();
    expect(screen.getByText("ops, critical")).toBeInTheDocument();
  });
});

describe("App routing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects to login when unauthenticated", () => {
    renderWithAuth(<App />, makeContext());
    expect(screen.getByText(/demo mode/i)).toBeInTheDocument();
  });

  it("renders dashboard route when authenticated", async () => {
    vi.mocked(apiModule.api.listSignals).mockResolvedValue(emptyPage);
    renderWithAuth(<App />, makeContext({ token: "test", role: "viewer" }));
    await waitFor(() => {
      expect(screen.getByText(/Signal Dashboard/i)).toBeInTheDocument();
    });
  });
});

const mockSignal: SignalRead = {
  id: "test-signal-123",
  workspace: "test-ws",
  project: "test-proj",
  content: "Test signal content for detail view",
  tags: ["test", "detail"],
  agent_id: "test-agent",
  created_at: "2024-01-15T10:30:00Z",
  updated_at: "2024-01-15T10:30:00Z",
  relevance_score: 0.75,
};

describe("SignalDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays signal details when loaded", async () => {
    vi.mocked(apiModule.api.getSignal).mockResolvedValue(mockSignal);

    renderWithAuth(<SignalDetail />, makeContext({ token: "test", role: "operator" }), "/signals/test-signal-123");

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading signal/i)).not.toBeInTheDocument();
    }, { timeout: 2000 });

    expect(screen.getByText(/signal test-sig/i)).toBeInTheDocument();
    expect(screen.getByText("test-ws")).toBeInTheDocument();
    expect(screen.getByText("test-proj")).toBeInTheDocument();
    expect(screen.getByText("Test signal content for detail view")).toBeInTheDocument();
    expect(screen.getByText("test, detail")).toBeInTheDocument();
    expect(screen.getByText("test-agent")).toBeInTheDocument();
    expect(screen.getByText(/0\.7500/)).toBeInTheDocument();
  });

  it("allows operator to edit signal content", async () => {
    vi.mocked(apiModule.api.getSignal).mockResolvedValue(mockSignal);
    vi.mocked(apiModule.api.updateSignal).mockResolvedValue({ ...mockSignal, content: "Updated content" });

    renderWithAuth(<SignalDetail />, makeContext({ token: "test", role: "operator" }), "/signals/test-signal-123");

    await waitFor(() => {
      expect(screen.queryByText(/loading signal/i)).not.toBeInTheDocument();
    }, { timeout: 2000 });

    expect(screen.getByText("Test signal content for detail view")).toBeInTheDocument();

    // Click edit button
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    // Verify edit form appears
    expect(screen.getByDisplayValue("Test signal content for detail view")).toBeInTheDocument();
    expect(screen.getByDisplayValue("test, detail")).toBeInTheDocument();
    expect(screen.getByDisplayValue("test-agent")).toBeInTheDocument();

    // Update content
    const textarea = screen.getByDisplayValue("Test signal content for detail view");
    fireEvent.change(textarea, { target: { value: "Updated content" } });

    // Submit
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(apiModule.api.updateSignal).toHaveBeenCalledWith(
        "test-signal-123",
        { content: "Updated content", tags: ["test", "detail"], agent_id: "test-agent" },
        "test"
      );
    });
  });

  it("shows error state when signal not found", async () => {
    vi.mocked(apiModule.api.getSignal).mockRejectedValueOnce(new ApiError(404, "Signal not found"));

    renderWithAuth(<SignalDetail />, makeContext({ token: "test", role: "viewer" }), "/signals/nonexistent");

    await waitFor(() => {
      expect(screen.queryByText(/loading signal/i)).not.toBeInTheDocument();
    }, { timeout: 2000 });

    await waitFor(() => {
      expect(screen.getByText(/signal not found/i)).toBeInTheDocument();
    });
  });

  it("allows admin to delete signal", async () => {
    vi.mocked(apiModule.api.getSignal).mockResolvedValue(mockSignal);
    vi.mocked(apiModule.api.deleteSignal).mockResolvedValue(undefined);

    renderWithAuth(<SignalDetail />, makeContext({ token: "test", role: "admin" }), "/signals/test-signal-123");

    await waitFor(() => {
      expect(screen.queryByText(/loading signal/i)).not.toBeInTheDocument();
    }, { timeout: 2000 });

    await waitFor(() => {
      expect(screen.getByText(/signal test-sig/i)).toBeInTheDocument();
    });

    // Click delete button and confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn().mockReturnValue(true);

    fireEvent.click(screen.getByRole("button", { name: /delete/i }));

    await waitFor(() => {
      expect(apiModule.api.deleteSignal).toHaveBeenCalledWith("test-signal-123", "test");
    });

    window.confirm = originalConfirm;
  });
});
