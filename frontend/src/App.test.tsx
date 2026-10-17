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
import { api, ApiError } from "./api/client";
import type { AuthContextType, UserRole, SignalPage } from "./types";

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
    vi.mocked(api.listSignals).mockResolvedValue(emptyPage);

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
    vi.mocked(api.listSignals).mockResolvedValue(pageWithData);

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
    vi.mocked(api.listSignals).mockResolvedValue(emptyPage);
    renderWithAuth(<App />, makeContext({ token: "test", role: "viewer" }));
    await waitFor(() => {
      expect(screen.getByText(/Signal Dashboard/i)).toBeInTheDocument();
    });
  });
});