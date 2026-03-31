import type { ScoreInfo } from "@/types";

interface ScoreCardProps {
  score: ScoreInfo;
}

interface ScoreCategory {
  label: string;
  color: string;
  bg: string;
  ring: string;
  glow: string;
}

function getCategory(score: number): ScoreCategory {
  if (score >= 80) return { label: "Sangat Baik", color: "text-emerald-400", bg: "bg-emerald-500/10", ring: "ring-emerald-500/50", glow: "shadow-emerald-500/20" };
  if (score >= 60) return { label: "Baik", color: "text-blue-400", bg: "bg-blue-500/10", ring: "ring-blue-500/50", glow: "shadow-blue-500/20" };
  if (score >= 40) return { label: "Cukup", color: "text-yellow-400", bg: "bg-yellow-500/10", ring: "ring-yellow-500/50", glow: "shadow-yellow-500/20" };
  return { label: "Perlu Perhatian", color: "text-red-400", bg: "bg-red-500/10", ring: "ring-red-500/50", glow: "shadow-red-500/20" };
}

function getRecommendationStyle(rec: ScoreInfo["recommendation"]): string {
  switch (rec) {
    case "Beli Kuat": return "bg-emerald-500 text-white";
    case "Beli": return "bg-emerald-500/20 text-emerald-400";
    case "Tahan": return "bg-yellow-500/20 text-yellow-400";
    case "Jual": return "bg-red-500/20 text-red-400";
    default: return "bg-gray-500/20 text-text-muted";
  }
}

interface ProgressBarProps {
  label: string;
  value: number | null;
}

function ProgressBar({ label, value }: ProgressBarProps) {
  const pct = value !== null ? Math.min(100, Math.max(0, value)) : 0;
  let barColor = "bg-red-500";
  if (pct >= 80) barColor = "bg-emerald-500";
  else if (pct >= 60) barColor = "bg-blue-500";
  else if (pct >= 40) barColor = "bg-yellow-500";

  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-text-secondary">
        <span>{label}</span>
        <span>{value !== null ? `${value.toFixed(0)}/100` : "N/A"}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-dark-bg">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ScoreCard({ score }: ScoreCardProps) {
  const category = getCategory(score.score);

  // score_factors from backend is an object {valuation, quality, momentum}, not string[]
  const rawFactors = score.score_factors;
  let factors: string[] = [];
  if (Array.isArray(rawFactors)) {
    factors = rawFactors.slice(0, 3);
  } else if (rawFactors && typeof rawFactors === "object") {
    const parts: string[] = [];
    const f = rawFactors as any;
    if (f.valuation?.available) parts.push(`Valuasi: ${f.valuation.score?.toFixed(0) ?? "N/A"}/100`);
    if (f.quality?.available) parts.push(`Kualitas: ${f.quality.score?.toFixed(0) ?? "N/A"}/100`);
    if (f.momentum?.available) parts.push(`Momentum: ${f.momentum.score?.toFixed(0) ?? "N/A"}/100`);
    factors = parts.slice(0, 3);
  }

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-6">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-text-secondary">
        Skor Saham
      </h2>

      {/* Score circle */}
      <div className="mb-4 flex items-center gap-4">
        <div
          className={`flex h-20 w-20 shrink-0 items-center justify-center rounded-full ring-4 ${category.ring} ${category.bg} shadow-lg ${category.glow}`}
        >
          <span className={`text-2xl font-bold ${category.color}`}>
            {score.score.toFixed(0)}
          </span>
        </div>
        <div>
          <p className={`text-base font-semibold ${category.color}`}>{category.label}</p>
          {score.recommendation && (
            <span
              className={`mt-1 inline-block rounded-full px-3 py-0.5 text-xs font-semibold ${getRecommendationStyle(score.recommendation)}`}
            >
              {score.recommendation}
            </span>
          )}
        </div>
      </div>

      {/* Breakdown */}
      <div className="mb-4 space-y-3">
        <ProgressBar label="Valuasi" value={score.valuation_score} />
        <ProgressBar label="Kualitas" value={score.quality_score} />
        <ProgressBar label="Momentum" value={score.momentum_score} />
      </div>

      {/* Factors */}
      {factors.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs font-medium text-text-muted">Faktor Pendukung</p>
          <ul className="space-y-1">
            {factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <span className="mt-0.5 text-emerald-400">✓</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-[10px] leading-relaxed text-text-muted">
        * Skor bersifat informatif dan bukan merupakan rekomendasi investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab investor.
      </p>
    </div>
  );
}
