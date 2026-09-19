export function LoadingSkeleton({ type = "card" }: { type?: "card" | "table" | "detail" }) {
  if (type === "table") {
    return (
      <div className="skeleton-wrap">
        <div className="skeleton-row skeleton-header-row" />
        <div className="skeleton-row" />
        <div className="skeleton-row" />
        <div className="skeleton-row" />
      </div>
    );
  }

  if (type === "detail") {
    return (
      <div className="skeleton-wrap">
        <div className="skeleton-block skeleton-title" />
        <div className="skeleton-block skeleton-chart" />
        <div className="skeleton-row" />
      </div>
    );
  }

  return (
    <div className="skeleton-grid">
      <div className="skeleton-card" />
      <div className="skeleton-card" />
      <div className="skeleton-card" />
    </div>
  );
}
