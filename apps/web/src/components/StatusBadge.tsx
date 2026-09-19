export function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toUpperCase();

  let variantClass = "status-badge-neutral";
  if (s === "SUCCESS" || s === "ACTIVE") {
    variantClass = "status-badge-success";
  } else if (s === "RETRIED") {
    variantClass = "status-badge-warning";
  } else if (s === "FAILED" || s === "INACTIVE") {
    variantClass = "status-badge-danger";
  }

  return <span className={`status-badge ${variantClass}`}>{s}</span>;
}
