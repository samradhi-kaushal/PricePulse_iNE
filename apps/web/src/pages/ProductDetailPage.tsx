import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getProduct, trackProduct, listTrackedProducts, stopTracking, manualScrape, getPriceHistory, getScrapeLogs } from "../api";
import type { Product, TrackedProduct, PricePoint, Attempt } from "../types";
import { PriceDisplay } from "../components/PriceDisplay";
import { StockBadge } from "../components/StockBadge";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { PriceChart } from "../components/PriceChart";

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [tracked, setTracked] = useState<TrackedProduct | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const pData = await getProduct(id).catch(() => null);
      setProduct(pData);

      const tList = await listTrackedProducts();
      const matched = tList.items.find(
        (tp) => tp.id === id || tp.product?.id === id || tp.product?.external_id === id
      );

      if (matched) {
        setTracked(matched);
        const [hRes, sRes] = await Promise.all([
          getPriceHistory(matched.id).catch(() => ({ items: [] })),
          getScrapeLogs(matched.id).catch(() => ({ items: [] })),
        ]);
        setHistory(hRes.items || []);
        setAttempts(sRes.items || []);
      } else {
        setTracked(null);
        setHistory([]);
        setAttempts([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load product.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const handleStartTracking = async () => {
    if (!id) return;
    setScraping(true);
    try {
      await trackProduct(id);
      await fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not start tracking.");
    } finally {
      setScraping(false);
    }
  };

  const handleStopTracking = async () => {
    if (!tracked) return;
    if (!window.confirm("Stop tracking this product? Existing price history will be kept.")) return;
    try {
      await stopTracking(tracked.id);
      await fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not stop tracking.");
    }
  };

  const handleScrapeNow = async () => {
    if (!tracked) return;
    setScraping(true);
    try {
      await manualScrape(tracked.id);
      await fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Scrape failed.");
    } finally {
      setScraping(false);
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorState message={error} onRetry={fetchDetail} />;
  if (!product && !tracked) return <ErrorState message="Product not found." onRetry={() => navigate("/products")} />;

  const name = product?.name ?? tracked?.product?.name ?? tracked?.name ?? "Product Detail";
  const brand = product?.brand ?? tracked?.product?.brand ?? "INE";
  const category = product?.category ?? tracked?.product?.category ?? "General";
  const sku = product?.sku ?? tracked?.product?.sku ?? product?.external_id ?? "N/A";
  const lastPrice = tracked?.latest_price ?? tracked?.latestPrice;
  const isCurrentlyTracked = tracked?.is_active ?? tracked?.active ?? false;

  return (
    <div className="page-content">
      <div className="detail-top-bar">
        <Link to="/products" className="back-link">← Back to Products</Link>
      </div>

      <div className="detail-header-card">
        <div className="detail-header-main">
          <div>
            <div className="detail-tags">
              <span className="badge-category">{category}</span>
              <span className="badge-brand">{brand}</span>
              <span className="badge-sku">SKU: {sku}</span>
            </div>
            <h1 className="detail-title">{name}</h1>
          </div>

          <div className="detail-tracking-box">
            {isCurrentlyTracked ? (
              <div className="tracking-status-group">
                <StatusBadge status="Active" />
                <span className="tracking-text">Currently Tracking</span>
                <div className="tracking-btn-group">
                  <button className="btn btn-secondary" onClick={handleScrapeNow} disabled={scraping}>
                    {scraping ? "Scraping..." : "Scrape Now"}
                  </button>
                  <button className="btn btn-danger-outline" onClick={handleStopTracking}>
                    Stop Tracking
                  </button>
                </div>
              </div>
            ) : (
              <div className="tracking-status-group">
                <StatusBadge status="Inactive" />
                <span className="tracking-text">Not Tracked</span>
                <button className="btn btn-primary" onClick={handleStartTracking} disabled={scraping}>
                  {scraping ? "Starting..." : "Start Tracking"}
                </button>
              </div>
            )}
          </div>
        </div>

        {isCurrentlyTracked && (
          <div className="detail-live-metrics">
            <div className="live-metric-item">
              <span className="metric-label">Current Price</span>
              {lastPrice ? (
                <PriceDisplay price={lastPrice.price} currency={lastPrice.currency} className="metric-val-large" />
              ) : (
                <span className="text-muted font-small">Waiting for first successful scrape</span>
              )}
            </div>

            <div className="live-metric-item">
              <span className="metric-label">Stock Status</span>
              <StockBadge stock={lastPrice?.stock} />
            </div>

            <div className="live-metric-item">
              <span className="metric-label">Last Check</span>
              <span className="metric-val-small">
                {lastPrice?.recorded_at ? new Date(lastPrice.recorded_at).toLocaleString() : "Awaiting scrape"}
              </span>
            </div>
          </div>
        )}
      </div>

      {isCurrentlyTracked && (
        <section className="dashboard-card margin-top">
          <div className="card-header">
            <h3>Price Trend</h3>
          </div>
          <PriceChart history={history} />
        </section>
      )}

      {isCurrentlyTracked && (
        <div className="detail-grid margin-top">
          <section className="dashboard-card">
            <div className="card-header">
              <h3>Price Observations</h3>
            </div>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Observed At</th>
                    <th>Price</th>
                    <th>Stock</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((pt) => (
                    <tr key={pt.id}>
                      <td>{pt.recorded_at ? new Date(pt.recorded_at).toLocaleString() : "-"}</td>
                      <td><PriceDisplay price={pt.price} currency={pt.currency} /></td>
                      <td><StockBadge stock={pt.stock} /></td>
                    </tr>
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td colSpan={3} className="text-center text-muted">No confirmed observations yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="dashboard-card">
            <div className="card-header">
              <h3>Scrape History Log</h3>
            </div>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Attempted At</th>
                    <th>Attempt</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attempts.map((att) => (
                    <tr key={att.id}>
                      <td>{att.attempted_at ? new Date(att.attempted_at).toLocaleString() : "-"}</td>
                      <td>#{att.attempt_number}</td>
                      <td><StatusBadge status={att.status} /></td>
                    </tr>
                  ))}
                  {attempts.length === 0 && (
                    <tr>
                      <td colSpan={3} className="text-center text-muted">No scrape logs recorded yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
