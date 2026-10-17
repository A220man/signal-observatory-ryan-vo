/**
 * Top navigation bar with branding, links, and auth status.
 */
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";

const navLinks = [
  { to: "/", label: "Dashboard" },
  { to: "/signals/new", label: "New Signal" },
  { to: "/handoff", label: "Handoff Briefing" },
];

export const HeaderNav: React.FC = () => {
  const { token, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header
      style={{
        background: "var(--surface)",
        borderBottom: "1px solid var(--border)",
        padding: "0.75rem 1.5rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <nav style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
        <a
          href="/"
          style={{
            fontWeight: "bold",
            fontSize: "1.25rem",
            color: "var(--accent)",
            textDecoration: "none",
          }}
        >
          Signal Observatory
        </a>
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            style={({ isActive }) => ({
              color: isActive ? "var(--text)" : "var(--text-muted)",
              textDecoration: "none",
              padding: "0.25rem 0.5rem",
              borderBottom: isActive ? "2px solid var(--accent)" : "none",
            })}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {token && (
          <>
            <span
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                textTransform: "capitalize",
              }}
            >
              {role}
            </span>
            <button
              onClick={handleLogout}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
              }}
            >
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
};