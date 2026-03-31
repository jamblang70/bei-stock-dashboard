import type { FundamentalsData } from "@/types";

interface MetricsCardProps {
  fundamentals: FundamentalsData | null;
}

function fmt(value: number | null | undefined, decimals = 2, suffix = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(decimals)}${suffix}`;
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-text-muted">{label}</span>
      <span className={`text-base font-semibold ${value === "N/A" ? "text-text-muted" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}

function Divider() {
  return <div className="hidden sm:block w-px bg-dark-border" />;
}

export default function MetricsCard({ fundamentals: f }: MetricsCardProps) {
  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-text-secondary">
        Metrik Utama
      </h2>

      {/* Row 1: Valuasi */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-0 sm:divide-x sm:divide-dark-border">
        <div className="sm:pr-4">
          <MetricItem label="PER" value={fmt(f?.per, 2, "x")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="PBV" value={fmt(f?.pbv, 2, "x")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="EV/EBITDA" value={fmt(f?.ev_ebitda, 2, "x")} />
        </div>
        <div className="sm:pl-4">
          <MetricItem label="EPS" value={fmt(f?.eps, 2)} />
        </div>
      </div>

      <div className="my-4 border-t border-dark-border/50" />

      {/* Row 2: Profitabilitas */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-0 sm:divide-x sm:divide-dark-border">
        <div className="sm:pr-4">
          <MetricItem label="ROE" value={fmt(f?.roe, 2, "%")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="ROA" value={fmt(f?.roa, 2, "%")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="Net Margin" value={fmt(f?.net_profit_margin, 2, "%")} />
        </div>
        <div className="sm:pl-4">
          <MetricItem label="Div. Yield" value={fmt(f?.dividend_yield, 2, "%")} />
        </div>
      </div>

      <div className="my-4 border-t border-dark-border/50" />

      {/* Row 3: Risiko & Likuiditas */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-0 sm:divide-x sm:divide-dark-border">
        <div className="sm:pr-4">
          <MetricItem label="DER" value={fmt(f?.debt_to_equity, 2, "x")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="Current Ratio" value={fmt(f?.current_ratio, 2, "x")} />
        </div>
        <div className="sm:px-4">
          <MetricItem label="Beta" value={fmt(f?.beta, 2)} />
        </div>
        <div className="sm:pl-4">
          <MetricItem label="Volatilitas" value={fmt(f?.volatility_30d, 2, "%")} />
        </div>
      </div>
    </div>
  );
}
