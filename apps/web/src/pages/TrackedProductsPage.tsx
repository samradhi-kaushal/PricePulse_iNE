import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listTrackedProducts, stopTracking, manualScrape } from "../api";
import type { TrackedProduct } from "../types";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { PriceDisplay } from "../components/PriceDisplay";
import { StockBadge } from "../components/StockBadge";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { ConfirmDialog } from "../components/ConfirmDialog";

import { updateTrackedProductInterval } from "../api/tracking";

export function TrackedProductsPage() {
  const [products, setProducts] = useState<TrackedProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [untrackTarget, setUntrackTarget] = useState<TrackedProduct | null>(null);

  const navigate = useNavigate();

  const fetchTracked = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listTrackedProducts();
      setProducts(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tracked products.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTracked();
  }, [fetchTracked]);

  const handleManualScrape = async (id: string) => {
    setActionId(id);
    try {
      await manualScrape(id);
      await fetchTracked();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Manual scrape failed.");
    } finally {
      setActionId(null);
    }
  };

  const handleIntervalChange = async (id: string, newInterval: number) => {
    try {
      await updateTrackedProductInterval(id, newInterval);
      await fetchTracked();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update scrape interval.");
    }
  };

  const handleConfirmUntrack = async () => {
    if (!untrackTarget) return;
    try {
      await stopTracking(untrackTarget.id);
      setUntrackTarget(null);
      await fetchTracked();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to untrack product.");
    }
  };

  return (
    <div className="page-content">
      <PageHeader
        title="Tracked Products"
        subtitle="Manage active price and stock monitoring across your tracked items."
        action={
          <Link to="/products" className="btn btn-primary">
            + Add Product
          </Link>
        }
      />

      {loading ? (
        <LoadingSkeleton type="table" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchTracked} />
      ) : products.length === 0 ? (
        <EmptyState
          title="No products are being tracked yet."
          message="Search the INE Store catalogue to start tracking product prices."
          action={<Link to="/products" className="btn btn-primary">Find a product</Link>}
        />
      ) : (
        <div className="dashboard-card">
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Current Price</th>
                  <th>Stock</th>
                  <th>Frequency</th>
                  <th>Next Scrape</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((tp) => {
                  const pname = tp.product?.name ?? tp.name ?? "Product";
                  const pid = tp.product?.id ?? tp.id;
                  const lastPrice = tp.latest_price ?? tp.latestPrice;
                  const isActive = tp.is_active ?? tp.active ?? true;
                  const interval = tp.scrape_interval_hours ?? 2;

                  return (
                    <tr key={tp.id}>
                      <td className="font-medium">
                        <div>{pname}</div>
                        <small className="text-muted">SKU: {tp.product?.sku || tp.product?.external_id || "N/A"}</small>
                      </td>
                      <td><PriceDisplay price={lastPrice?.price} currency={lastPrice?.currency} /></td>
                      <td><StockBadge stock={lastPrice?.stock} /></td>
                      <td>
                        <select
                          value={interval}
                          onChange={(e) => handleIntervalChange(tp.id, Number(e.target.value))}
                          style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            background: "rgba(255,255,255,0.05)",
                            color: "#e5e7eb",
                            border: "1px solid rgba(255,255,255,0.15)",
                            fontSize: "0.8rem"
                          }}
                        >
                          <option value={2} style={{ background: "#1e293b", color: "#fff" }}>Every 2 hours</option>
                          <option value={4} style={{ background: "#1e293b", color: "#fff" }}>Every 4 hours</option>
                          <option value={6} style={{ background: "#1e293b", color: "#fff" }}>Every 6 hours</option>
                          <option value={12} style={{ background: "#1e293b", color: "#fff" }}>Every 12 hours</option>
                          <option value={24} style={{ background: "#1e293b", color: "#fff" }}>Every 24 hours</option>
                        </select>
                      </td>
                      <td className="text-muted font-small">
                        {tp.next_scrape_at ? new Date(tp.next_scrape_at).toLocaleString() : "Scheduled"}
                      </td>
                      <td><StatusBadge status={isActive ? "Active" : "Inactive"} /></td>
                      <td>
                        <div className="table-actions">
                          <button className="btn-table" onClick={() => navigate(`/products/${pid}`)}>View</button>
                          <button className="btn-table" onClick={() => navigate(`/tracked/${tp.id}/history`)}>History</button>
                          <button
                            className="btn-table btn-table-primary"
                            disabled={actionId === tp.id}
                            onClick={() => handleManualScrape(tp.id)}
                          >
                            {actionId === tp.id ? "Scraping..." : "Scrape Now"}
                          </button>
                          <button
                            className="btn-table btn-table-danger"
                            onClick={() => setUntrackTarget(tp)}
                          >
                            Stop Tracking
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}


      <ConfirmDialog
        isOpen={!!untrackTarget}
        title="Stop Tracking Product"
        message={`Are you sure you want to stop tracking "${untrackTarget?.product?.name ?? untrackTarget?.name}"? Its price history will be preserved.`}
        confirmText="Stop Tracking"
        onConfirm={handleConfirmUntrack}
        onCancel={() => setUntrackTarget(null)}
      />
    </div>
  );
}
