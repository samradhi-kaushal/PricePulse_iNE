import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getDashboard, getPriceHistory } from "../api";
import type { DashboardData, PricePoint } from "../types";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { PriceDisplay } from "../components/PriceDisplay";
import { StockBadge } from "../components/StockBadge";
import { PriceChart } from "../components/PriceChart";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboard();
      setData(res);
      const recentList = res && res.recent_tracked_products ? res.recent_tracked_products : [];
      if (recentList.length > 0 && recentList[0]) {
        const firstId = recentList[0].id;
        const hRes = await getPriceHistory(firstId).catch(() => ({ items: [] }));
        setHistory(hRes.items || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (loading) return <LoadingSkeleton type="card" />;
  if (error) return <ErrorState message={error} onRetry={fetchDashboard} />;
  if (!data) return <EmptyState title="No Data" message="Unable to retrieve dashboard stats." />;

  return (
    <div className="page-content">
      <PageHeader
        title="Price Tracking Overview"
        subtitle="Monitor your tracked INE products and recent scraping activity."
      />

      <div className="stats-grid">
        <StatCard title="Tracked Products" value={data.tracked_product_count} icon="📦" />
        <StatCard title="Successful Scrapes" value={data.successful_scrape_count} icon="✓" />
        <StatCard title="Active Alerts" value={data.unread_alert_count ?? 0} icon="🔔" />
        <StatCard title="Failed Scrapes" value={data.failed_scrape_count} icon="⚠️" />
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-card">
          <div className="card-header">
            <h3>Multi-Product Overview</h3>
            <Link to="/tracked" className="link-action">View all →</Link>
          </div>
          {data.recent_tracked_products.length === 0 ? (
            <EmptyState
              title="No products tracked yet"
              message="Start tracking products from the INE Store catalogue."
              action={<Link to="/products" className="btn btn-primary">Find a product</Link>}
            />
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Current Price</th>
                    <th>Stock</th>
                    <th>Next Scrape</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_tracked_products.map((tp) => {
                    const pname = tp.product?.name ?? tp.name ?? "Product";
                    const lastPrice = tp.latest_price ?? tp.latestPrice;
                    const isActive = tp.is_active ?? tp.active ?? true;

                    return (
                      <tr key={tp.id}>
                        <td className="font-medium">{pname}</td>
                        <td><PriceDisplay price={lastPrice?.price} currency={lastPrice?.currency} /></td>
                        <td><StockBadge stock={lastPrice?.stock} /></td>
                        <td className="text-muted font-small">
                          {tp.next_scrape_at ? new Date(tp.next_scrape_at).toLocaleTimeString() : "-"}
                        </td>
                        <td><StatusBadge status={isActive ? "Active" : "Inactive"} /></td>
                        <td>
                          <div className="table-actions">
                            <Link to={`/products/${tp.product?.id ?? tp.id}`} className="btn-table">View</Link>
                            <Link to={`/tracked/${tp.id}/history`} className="btn-table">History</Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="dashboard-card">
          <div className="card-header">
            <h3>Recent Scrape Activity</h3>
            <Link to="/scrapes" className="link-action">View log →</Link>
          </div>
          {data.recent_scrape_activity.length === 0 ? (
            <EmptyState title="No scrape activity" message="Scrape attempts will appear here." />
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Attempt</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_scrape_activity.map((attempt) => {
                    const pname = attempt.product_name ?? "Product";
                    const tStr = attempt.attempted_at ?? attempt.started_at ?? "";
                    return (
                      <tr key={attempt.id}>
                        <td className="font-medium">{pname}</td>
                        <td>#{attempt.attempt_number}</td>
                        <td><StatusBadge status={attempt.status} /></td>
                        <td className="text-muted">{tStr ? new Date(tStr).toLocaleTimeString() : "-"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {data.recent_changes && data.recent_changes.length > 0 && (
        <section className="dashboard-card margin-top">
          <div className="card-header">
            <h3>Recent Price & Stock Changes</h3>
          </div>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Event</th>
                  <th>Previous</th>
                  <th>Current</th>
                  <th>Detected Time</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_changes.map((chg) => (
                  <tr key={chg.id}>
                    <td className="font-medium">{chg.product_name}</td>
                    <td>
                      <StatusBadge
                        status={
                          chg.change_type.includes("INCREASE") ? "RETRIED" : "SUCCESS"
                        }
                      />
                      {" "}
                      {chg.change_type.replace("_", " ")}
                    </td>
                    <td className="text-muted">{chg.previous_value}</td>
                    <td className="font-medium">{chg.current_value}</td>
                    <td className="text-muted font-small">
                      {new Date(chg.detected_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="dashboard-card margin-top">
        <div className="card-header">
          <h3>Price Movement</h3>
          <span className="text-muted font-small">Tracked Product Trend</span>
        </div>
        <PriceChart history={history} />
      </section>
    </div>
  );
}

