export function StockBadge({ stock }: { stock?: number | null }) {
  if (stock === null || stock === undefined) {
    return <span className="stock-badge stock-unknown">Stock unavailable</span>;
  }

  if (stock === 0) {
    return <span className="stock-badge stock-out">Out of stock</span>;
  }

  return <span className="stock-badge stock-in">{stock} left</span>;
}
