import type { FundamentalsData } from "@/types";

interface AnalysisTabProps {
  fundamentals: FundamentalsData | null;
}

function fmt(value: number | null, decimals = 2, suffix = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(decimals)}${suffix}`;
}

interface MetricRowProps {
  label: string;
  value: string;
  note?: string;
}

function MetricRow({ label, value, note }: MetricRowProps) {
  return (
    <div className="flex items-center justify-between py-2 text-sm">
      <span className="text-text-secondary">{label}</span>
      <div className="text-right">
        <span className={`font-medium ${value === "N/A" ? "text-text-muted" : "text-text-primary"}`}>
          {value}
        </span>
        {note && <p className="text-xs text-text-muted">{note}</p>}
      </div>
    </div>
  );
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

function Section({ title, children }: SectionProps) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</h3>
      <div className="divide-y divide-dark-border/50 rounded-lg border border-dark-border bg-dark-bg/50 px-4">
        {children}
      </div>
    </div>
  );
}

export default function AnalysisTab({ fundamentals: f }: AnalysisTabProps) {
  const noHistorical = "Data historis tidak tersedia";

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-6">
      <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-text-secondary">
        Analisa Fundamental
      </h2>

      <div className="space-y-5">
        {/* Valuasi */}
        <Section title="Valuasi">
          <MetricRow
            label="PER"
            value={fmt(f?.per ?? null, 2, "x")}
            note={f?.per === null ? noHistorical : undefined}
          />
          <MetricRow
            label="PBV"
            value={fmt(f?.pbv ?? null, 2, "x")}
            note={f?.pbv === null ? noHistorical : undefined}
          />
          <MetricRow
            label="EV/EBITDA"
            value={fmt(f?.ev_ebitda ?? null, 2, "x")}
            note={f?.ev_ebitda === null ? noHistorical : undefined}
          />
        </Section>

        {/* Kualitas Fundamental */}
        <Section title="Kualitas Fundamental">
          <MetricRow label="ROE" value={fmt(f?.roe ?? null, 2, "%")} />
          <MetricRow label="ROA" value={fmt(f?.roa ?? null, 2, "%")} />
          <MetricRow label="DER" value={fmt(f?.debt_to_equity ?? null, 2, "x")} />
          <MetricRow label="Current Ratio" value={fmt(f?.current_ratio ?? null, 2, "x")} />
          <MetricRow label="Net Profit Margin" value={fmt(f?.net_profit_margin ?? null, 2, "%")} />
        </Section>

        {/* Risiko */}
        <Section title="Risiko">
          <MetricRow label="Beta" value={fmt(f?.beta ?? null, 2)} />
          <MetricRow label="Volatilitas 30 Hari" value={fmt(f?.volatility_30d ?? null, 2, "%")} />
          <MetricRow label="DER" value={fmt(f?.debt_to_equity ?? null, 2, "x")} />
        </Section>
      </div>

      {!f && (
        <p className="mt-4 text-center text-sm text-text-muted">
          Data fundamental tidak tersedia
        </p>
      )}
    </div>
  );
}
