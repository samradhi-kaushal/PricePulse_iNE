import { NavLink } from "react-router-dom";

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const links = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/products", label: "Products", icon: "📦" },
    { to: "/tracked", label: "Tracked Products", icon: "🎯" },
    { to: "/history", label: "Price History", icon: "📈" },
    { to: "/scrapes", label: "Scrape Activity", icon: "⚡" },
  ];

  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-logo">P</div>
          <div className="brand-text">
            <span className="brand-title">PricePulse</span>
            <span className="brand-subtitle">Track the prices that matter.</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="nav-icon">{link.icon}</span>
              <span className="nav-label">{link.label}</span>
            </NavLink>
          ))}

          <div className="nav-divider" />

          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            onClick={onClose}
          >
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">Settings</span>
          </NavLink>
        </nav>
      </aside>
    </>
  );
}
