import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PricePoint } from "../types";

export function PriceChart({ history }: { history: PricePoint[] }) {
  if (!history || history.length <= 1) {
    return (
      <div className="empty-chart-notice">
        Price movement will appear after multiple successful scrapes.
      </div>
    );
  }

  const chartData = [...history].reverse().map((point) => {
    const rawDate = point.recorded_at ?? point.observed_at ?? "";
    return {
      ...point,
      label: rawDate ? new Date(rawDate).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "",
    };
  });

  const currency = history[0]?.currency || "INR";

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 12, right: 16, left: 12, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 12 }} width={72} />
          <Tooltip
            formatter={(value: any) => [`${currency} ${Number(value).toLocaleString("en-IN")}`, "Price"]}
            contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
          />
          <Line type="monotone" dataKey="price" stroke="#0f172a" strokeWidth={2.5} dot={{ r: 4, fill: "#0f172a" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
