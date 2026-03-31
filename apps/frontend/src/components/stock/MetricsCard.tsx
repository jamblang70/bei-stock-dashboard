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
      <span className="text-xs text-text-muted">{label}</span>
      <span className={`text-lg font-semibold ${value === "N/A" ? "text-text-muted" : "text-text-primary"}`}>
        {value}
      </span>
      {description && <span className="text-xs text-text-muted">{description}</span>}
    </div>
  );
}

export default function MetricsCard({ fundamentals }: MetricsCardProps) {
  const per = fmt(fundamentals?.per ?? null, 2, "x");
  const pbv = fmt(fundamentals?.pbv ?? null, 2, "x");
  const roe = fmt(fundamentals?.roe ?? null, 2, "%");
  const divYield = fmt(fundamentals?.dividend_yield ?? null, 2, "%");

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-6">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-text-secondary">
        Metrik Utama
      </h2>
      <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
        <MetricItem label="PER" value={per} description="Price to Earnings" />
        <div className="border-l border-dark-border pl-6">
          <MetricItem label="PBV" value={pbv} description="Price to Book Value" />
        </div>
        <div className="border-l border-dark-border pl-6 max-sm:border-l-0 max-sm:pl-0">
          <MetricItem label="ROE" value={roe} description="Return on Equity" />
        </div>
        <div className="border-l border-dark-border pl-6">
          <MetricItem label="Div. Yield" value={divYield} description="Dividend Yield" />
        </div>
      </div>
    </div>
  );
}
