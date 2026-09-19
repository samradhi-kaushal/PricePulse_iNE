import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { listTrackedProducts, getPriceHistory } from "../api";
import type { TrackedProduct, PricePoint } from "../types";
import { PageHeader } from "../components/PageHeader";
import { PriceDisplay } from "../components/PriceDisplay";
import { StockBadge } from "../components/StockBadge";
import { PriceChart } from "../components/PriceChart";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";

export function PriceHistoryPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();

  const [trackedProducts, setTrackedProducts] = useState<TrackedProduct[]>([]);
  const [selectedTracked, setSelectedTracked] = useState<TrackedProduct | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listTrackedProducts();
      const items = res.items || [];
      setTrackedProducts(items);

      if (items.length > 0) {
        const matched = id ? items.find((tp) => tp.id === id || tp.product?.id === id) : items[0];
        const activeItem = matched || items[0];
        if (activeItem) {
          setSelectedTracked(activeItem);
          const hRes = await getPriceHistory(activeItem.id);
          setHistory(hRes.items || []);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load price history.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const handleSelectProduct = async (tpId: string) => {
    const item = trackedProducts.find((tp) => tp.id === tpId);
    if (!item) return;
    setSelectedTracked(item);
    navigate(`/tracked/${item.id}/history`, { replace: true });

    try {
      const hRes = await getPriceHistory(item.id);
      setHistory(hRes.items || []);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not load history for selected item.");
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorState message={error} onRetry={fetchInitialData} />;

  if (trackedProducts.length === 0) {
    return (
      <div className="page-content">
        <PageHeader title="Price History" subtitle="Track historical price trends over time." />
        <EmptyState
          title="No price history available"
          message="Start tracking products to view historical price charts and observations."
          action={<button className="btn btn-primary" onClick={() => navigate("/products")}>Find a product</button>}
        />
      </div>
    );
  }

  const prices = history.map((pt) => pt.price).filter((p) => p > 0);
  const currentPrice = prices.length > 0 ? prices[0] : null;
  const previousPrice = prices.length > 1 ? prices[1] : null;
  const highestPrice = prices.length > 0 ? Math.max(...prices) : null;
  const lowestPrice = prices.length > 0 ? Math.min(...prices) : null;
  const currency = history[0]?.currency || "INR";

  const selectedName = selectedTracked?.product?.name ?? selectedTracked?.name ?? "Selected Product";

  return (
    <div className="page-content">
      <PageHeader
        title="Price History"
        subtitle="Analyze real recorded prices and stock observations."
      />

      <div className="history-selector-card">
        <label className="select-label">Select Tracked Product:</label>
        <select
          className="select-input"
          value={selectedTracked?.id || ""}
          onChange={(e) => handleSelectProduct(e.target.value)}
        >
          {trackedProducts.map((tp) => (
            <option key={tp.id} value={tp.id}>
              {tp.product?.name ?? tp.name ?? "Product"} (SKU: {tp.product?.sku || tp.product?.external_id || "N/A"})
            </option>
          ))}
        </select>
      </div>

      <div className="stats-grid margin-top">
        <StatCard
          title="Current Price"
          value={currentPrice != null ? `${currency} ${currentPrice.toLocaleString("en-IN")}` : "N/A"}
          subtext="Latest observation"
        />
        <StatCard
          title="Previous Price"
          value={previousPrice != null ? `${currency} ${previousPrice.toLocaleString("en-IN")}` : "N/A"}
          subtext="Prior check"
        />
        <StatCard
          title="Highest Recorded"
          value={highestPrice != null ? `${currency} ${highestPrice.toLocaleString("en-IN")}` : "N/A"}
          subtext="Peak price"
        />
        <StatCard
          title="Lowest Recorded"
          value={lowestPrice != null ? `${currency} ${lowestPrice.toLocaleString("en-IN")}` : "N/A"}
          subtext="Lowest price"
        />
      </div>

      <section className="dashboard-card margin-top">
        <div className="card-header">
          <h3>Price Trend: {selectedName}</h3>
        </div>
        <PriceChart history={history} />
      </section>

      <section className="dashboard-card margin-top">
        <div className="card-header">
          <h3>Recorded Observations Table</h3>
        </div>
        {history.length === 0 ? (
          <EmptyState title="No confirmed observations" message="This product has not completed two successful checks yet." />
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Price</th>
                  <th>Stock</th>
                </tr>
              </thead>
              <tbody>
                {history.map((pt) => {
                  const tStr = pt.recorded_at ?? pt.observed_at ?? "";
                  return (
                    <tr key={pt.id}>
                      <td>{tStr ? new Date(tStr).toLocaleString() : "-"}</td>
                      <td><PriceDisplay price={pt.price} currency={pt.currency} /></td>
                      <td><StockBadge stock={pt.stock} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
