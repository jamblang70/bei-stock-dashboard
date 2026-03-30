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
      <span className="text-gray-600">{label}</span>
      <div className="text-right">
        <span className={`font-medium ${value === "N/A" ? "text-gray-400" : "text-gray-900"}`}>
          {value}
        </span>
        {note && <p className="text-xs text-gray-400">{note}</p>}
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
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">{title}</h3>
      <div className="divide-y divide-gray-100 rounded-lg border border-gray-100 bg-gray-50 px-4">
        {children}
      </div>
    </div>
  );
}

export default function AnalysisTab({ fundamentals: f }: AnalysisTabProps) {
  const noHistorical = "Data historis tidak tersedia";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-gray-500">
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
        <p className="mt-4 text-center text-sm text-gray-400">
          Data fundamental tidak tersedia
        </p>
      )}
    </div>
  );
}
