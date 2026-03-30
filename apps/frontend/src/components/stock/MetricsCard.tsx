import type { FundamentalsData } from "@/types";

interface MetricsCardProps {
  fundamentals: FundamentalsData | null;
}

function fmt(value: number | null, decimals = 2, suffix = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(decimals)}${suffix}`;
}

interface MetricItemProps {
  label: string;
  value: string;
  description?: string;
}

function MetricItem({ label, value, description }: MetricItemProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-lg font-semibold ${value === "N/A" ? "text-gray-400" : "text-gray-900"}`}>
        {value}
      </span>
      {description && <span className="text-xs text-gray-400">{description}</span>}
    </div>
  );
}

export default function MetricsCard({ fundamentals }: MetricsCardProps) {
  const per = fmt(fundamentals?.per ?? null, 2, "x");
  const pbv = fmt(fundamentals?.pbv ?? null, 2, "x");
  const roe = fmt(fundamentals?.roe ?? null, 2, "%");
  const divYield = fmt(fundamentals?.dividend_yield ?? null, 2, "%");

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
        Metrik Utama
      </h2>
      <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
        <MetricItem label="PER" value={per} description="Price to Earnings" />
        <MetricItem label="PBV" value={pbv} description="Price to Book Value" />
        <MetricItem label="ROE" value={roe} description="Return on Equity" />
        <MetricItem label="Div. Yield" value={divYield} description="Dividend Yield" />
      </div>
    </div>
  );
}
