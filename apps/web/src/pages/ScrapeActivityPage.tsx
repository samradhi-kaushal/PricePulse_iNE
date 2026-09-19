import { useEffect, useState, useCallback } from "react";
import { getScrapeLogs } from "../api";
import type { Attempt } from "../types";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { ErrorModal } from "../components/ErrorModal";

export function ScrapeActivityPage() {
  const [logs, setLogs] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedErrorAttempt, setSelectedErrorAttempt] = useState<Attempt | null>(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getScrapeLogs();
      setLogs(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scrape logs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  if (loading) return <LoadingSkeleton type="table" />;
  if (error) return <ErrorState message={error} onRetry={fetchLogs} />;

  const totalAttempts = logs.length;
  const successCount = logs.filter((l) => l.status.toUpperCase() === "SUCCESS").length;
  const retriedCount = logs.filter((l) => l.status.toUpperCase() === "RETRIED").length;
  const failedCount = logs.filter((l) => l.status.toUpperCase() === "FAILED").length;

  return (
    <div className="page-content">
      <PageHeader
        title="Scrape Activity"
        subtitle="Audit scrape execution, attempt history, and failure logs."
      />

      <div className="stats-grid">
        <StatCard title="Total Attempts" value={totalAttempts} icon="⚡" />
        <StatCard title="Successful" value={successCount} icon="✓" />
        <StatCard title="Retried" value={retriedCount} icon="↻" />
        <StatCard title="Failed" value={failedCount} icon="⚠️" />
      </div>

      {logs.length === 0 ? (
        <EmptyState title="No scrape logs recorded" message="Scrape attempt activity will appear here as items are monitored." />
      ) : (
        <div className="dashboard-card margin-top">
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Product</th>
                  <th>Attempt</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Error Detail</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const tStr = log.attempted_at ?? log.started_at ?? "";
                  const isFailed = log.status.toUpperCase() === "FAILED" || log.status.toUpperCase() === "RETRIED";

                  return (
                    <tr
                      key={log.id}
                      className={isFailed && log.error_message ? "row-clickable" : ""}
                      onClick={() => {
                        if (log.error_message) setSelectedErrorAttempt(log);
                      }}
                    >
                      <td className="font-small text-muted">
                        {tStr ? new Date(tStr).toLocaleString() : "-"}
                      </td>
                      <td className="font-medium">{log.product_name ?? "Product"}</td>
                      <td>#{log.attempt_number}</td>
                      <td><StatusBadge status={log.status} /></td>
                      <td className="font-small text-muted">{log.duration_ms ? `${log.duration_ms}ms` : "-"}</td>
                      <td className="font-small">
                        {log.error_message ? (
                          <span className="error-preview text-danger">
                            {log.error_code ? `[${log.error_code}] ` : ""}{log.error_message.slice(0, 45)}...
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ErrorModal
        attempt={selectedErrorAttempt}
        onClose={() => setSelectedErrorAttempt(null)}
      />
    </div>
  );
}
