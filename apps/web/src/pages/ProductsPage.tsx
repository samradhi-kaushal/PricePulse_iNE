import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { listProducts, trackProduct } from "../api";
import type { Product } from "../types";
import { PageHeader } from "../components/PageHeader";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const navigate = useNavigate();

  const fetchCatalogue = useCallback(async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await listProducts(searchQuery);
      setProducts(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load catalogue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCatalogue(query);
  }, [query, fetchCatalogue]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams(query ? { q: query } : {});
  };

  const handleTrack = async (productId: string) => {
    setBusyId(productId);
    try {
      await trackProduct(productId);
      fetchCatalogue(query);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not track product.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="page-content">
      <PageHeader
        title="Product Catalogue"
        subtitle="Find a product from the INE Store catalogue."
      />

      <section className="search-section">
        <form onSubmit={handleSearchSubmit} className="search-box-form">
          <input
            type="text"
            className="input-search"
            placeholder="Search by product name, brand, SKU, or category..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button
              type="button"
              className="btn-clear"
              onClick={() => {
                setQuery("");
                setSearchParams({});
              }}
            >
              ✕
            </button>
          )}
        </form>
      </section>

      {loading ? (
        <LoadingSkeleton type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchCatalogue(query)} />
      ) : products.length === 0 ? (
        <EmptyState
          title="No products found"
          message={query ? `No items matched "${query}". Try searching another name or brand.` : "Catalogue is currently empty."}
        />
      ) : (
        <div className="product-cards-grid">
          {products.map((product) => (
            <div key={product.id} className="product-light-card">
              <div className="product-card-top">
                <StatusBadge status={product.is_tracked ? "Active" : "Inactive"} />
                <span className="sku-tag">SKU: {product.sku || product.external_id}</span>
              </div>
              <h3 className="product-card-name">{product.name}</h3>
              <div className="product-card-meta">
                <span>Brand: <strong>{product.brand || "INE"}</strong></span>
                <span>Category: <strong>{product.category || "General"}</strong></span>
              </div>
              <div className="product-card-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => navigate(`/products/${product.id}`)}
                >
                  View Product
                </button>
                {product.is_tracked ? (
                  <button className="btn btn-disabled" disabled>
                    Tracked
                  </button>
                ) : (
                  <button
                    className="btn btn-primary"
                    disabled={busyId === product.id}
                    onClick={() => handleTrack(product.id)}
                  >
                    {busyId === product.id ? "Tracking..." : "Track"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
