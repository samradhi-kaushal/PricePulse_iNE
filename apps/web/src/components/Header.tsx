import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getUnreadAlertCount, listAlerts, markAlertRead, markAllAlertsRead } from "../api/alerts";
import type { AlertItem } from "../types";

export function Header({
  title,
  onRefresh,
  onToggleSidebar,
}: {
  title: string;
  onRefresh?: () => void;
  onToggleSidebar: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [unreadCount, setUnreadCount] = useState(0);
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const navigate = useNavigate();

  const fetchUnread = () => {
    getUnreadAlertCount()
      .then((res) => setUnreadCount(res.unread_count))
      .catch(() => {});
  };

  useEffect(() => {
    fetchUnread();
    const timer = setInterval(fetchUnread, 15000);
    return () => clearInterval(timer);
  }, []);

  const handleToggleAlerts = () => {
    if (!showAlertsModal) {
      listAlerts()
        .then((res) => setAlerts(res.items))
        .catch(() => {});
    }
    setShowAlertsModal((prev) => !prev);
  };

  const handleMarkRead = async (id: string) => {
    await markAlertRead(id).catch(() => {});
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  const handleMarkAllRead = async () => {
    await markAllAlertsRead().catch(() => {});
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    setUnreadCount(0);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery("");
    }
  };

  return (
    <header className="top-header">
      <div className="header-left">
        <button className="mobile-menu-btn" onClick={onToggleSidebar} aria-label="Toggle menu">
          ☰
        </button>
        <h1 className="header-page-title">{title}</h1>
      </div>

      <div className="header-right">
        <form onSubmit={handleSearchSubmit} className="global-search-form">
          <input
            type="text"
            className="global-search-input"
            placeholder="Search catalogue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="alert-bell-wrapper" style={{ position: "relative" }}>
          <button
            className="btn btn-secondary"
            onClick={handleToggleAlerts}
            aria-label="Alerts"
            style={{ position: "relative", padding: "8px 12px" }}
          >
            🔔
            {unreadCount > 0 && (
              <span
                style={{
                  position: "absolute",
                  top: "-4px",
                  right: "-4px",
                  background: "#ef4444",
                  color: "#ffffff",
                  fontSize: "10px",
                  fontWeight: "bold",
                  borderRadius: "9999px",
                  padding: "2px 6px",
                }}
              >
                {unreadCount}
              </span>
            )}
          </button>

          {showAlertsModal && (
            <div
              className="dashboard-card"
              style={{
                position: "absolute",
                right: 0,
                top: "45px",
                width: "360px",
                maxHeight: "400px",
                overflowY: "auto",
                zIndex: 1000,
                boxShadow: "0 10px 25px rgba(0,0,0,0.3)",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <h4 style={{ margin: 0 }}>System Alerts</h4>
                {unreadCount > 0 && (
                  <button className="btn btn-sm btn-secondary" onClick={handleMarkAllRead}>
                    Mark all read
                  </button>
                )}
              </div>

              {alerts.length === 0 ? (
                <p className="text-muted" style={{ fontSize: "0.875rem" }}>
                  No recent alerts.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {alerts.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        padding: "8px 12px",
                        borderRadius: "6px",
                        background: item.is_read ? "rgba(255,255,255,0.03)" : "rgba(59, 130, 246, 0.12)",
                        borderLeft: item.is_read ? "3px solid transparent" : "3px solid #3b82f6",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: "600", fontSize: "0.875rem" }}>{item.title}</div>
                        <div style={{ fontSize: "0.8rem", color: "#9ca3af" }}>{item.message}</div>
                        <div style={{ fontSize: "0.7rem", color: "#6b7280", marginTop: "2px" }}>
                          {new Date(item.created_at).toLocaleString()}
                        </div>
                      </div>
                      {!item.is_read && (
                        <button
                          style={{
                            background: "none",
                            border: "none",
                            color: "#3b82f6",
                            cursor: "pointer",
                            fontSize: "0.75rem",
                          }}
                          onClick={() => handleMarkRead(item.id)}
                        >
                          Read
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {onRefresh && (
          <button className="btn btn-secondary btn-icon-text" onClick={onRefresh}>
            <span>↻</span>
            <span className="btn-text">Refresh</span>
          </button>
        )}
      </div>
    </header>
  );
}

