/**
 * Signal Observatory — Main application router.
 *
 * Product: Long-term memory for agent coding CLIs and handoff between agent vendors.
 * Domain engine: TF-IDF + temporal decay relevance scoring (deterministic, offline).
 */
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./components/AuthProvider";
import { LoginPage } from "./components/LoginPage";
import { Dashboard } from "./components/Dashboard";
import { SignalForm } from "./components/SignalForm";
import { HandoffBriefing } from "./components/HandoffBriefing";
import { SignalDetail } from "./components/SignalDetail";
import { HeaderNav } from "./components/HeaderNav";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <>
      <HeaderNav />
      <main style={{ padding: "1.5rem", maxWidth: "960px", margin: "0 auto" }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/signals/new"
            element={
              <RequireAuth>
                <SignalForm />
              </RequireAuth>
            }
          />
          <Route
            path="/handoff"
            element={
              <RequireAuth>
                <HandoffBriefing />
              </RequireAuth>
            }
          />
          <Route
            path="/signals/:id"
            element={
              <RequireAuth>
                <SignalDetail />
              </RequireAuth>
            }
          />
        </Routes>
      </main>
    </>
  );
}