export function PriceDisplay({ price, currency = "INR", className = "" }: { price: number | null | undefined; currency?: string; className?: string }) {
  if (price === null || price === undefined) {
    return <span className={`price-display-none ${className}`}>No confirmed price</span>;
  }

  const formatted = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: currency,
    maximumFractionDigits: 0,
  }).format(price);

  return <span className={`price-display-val ${className}`}>{formatted}</span>;
}
