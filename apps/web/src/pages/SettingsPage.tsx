import { useEffect, useState } from "react";
import { PageHeader } from "../components/PageHeader";

export function SettingsPage() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

  useEffect(() => {
    fetch(`${apiBaseUrl}/health`)
      .then((res) => (res.ok ? setBackendStatus("online") : setBackendStatus("offline")))
      .catch(() => setBackendStatus("offline"));
  }, [apiBaseUrl]);

  return (
    <div className="page-content">
      <PageHeader
        title="Settings & System Overview"
        subtitle="Technical configuration and architecture status."
      />

      <div className="dashboard-grid">
        <section className="dashboard-card">
          <div className="card-header">
            <h3>Application Information</h3>
          </div>
          <div className="settings-list">
            <div className="settings-item">
              <span className="settings-label">Application Name</span>
              <span className="settings-value font-medium">PricePulse</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Tagline</span>
              <span className="settings-value text-muted">Track the prices that matter.</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Version</span>
              <span className="settings-value font-mono">2.0.0 (Django DRF Stack)</span>
            </div>
          </div>
        </section>

        <section className="dashboard-card">
          <div className="card-header">
            <h3>Backend Environment</h3>
          </div>
          <div className="settings-list">
            <div className="settings-item">
              <span className="settings-label">Backend Status</span>
              <span className={`status-badge ${backendStatus === "online" ? "status-badge-success" : backendStatus === "offline" ? "status-badge-danger" : "status-badge-warning"}`}>
                {backendStatus.toUpperCase()}
              </span>
            </div>
            <div className="settings-item">
              <span className="settings-label">API Base URL</span>
              <span className="settings-value font-mono">{apiBaseUrl}</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Database</span>
              <span className="settings-value text-muted">Supabase PostgreSQL</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Scraper Engine</span>
              <span className="settings-value text-muted">Python Playwright Sync Chromium</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
