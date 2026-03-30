import type { ScoreInfo } from "@/types";

interface ScoreCardProps {
  score: ScoreInfo;
}

interface ScoreCategory {
  label: string;
  color: string;
  bg: string;
  ring: string;
}

function getCategory(score: number): ScoreCategory {
  if (score >= 80) return { label: "Sangat Baik", color: "text-green-700", bg: "bg-green-100", ring: "ring-green-500" };
  if (score >= 60) return { label: "Baik", color: "text-blue-700", bg: "bg-blue-100", ring: "ring-blue-500" };
  if (score >= 40) return { label: "Cukup", color: "text-yellow-700", bg: "bg-yellow-100", ring: "ring-yellow-500" };
  return { label: "Perlu Perhatian", color: "text-red-700", bg: "bg-red-100", ring: "ring-red-500" };
}

function getRecommendationStyle(rec: ScoreInfo["recommendation"]): string {
  switch (rec) {
    case "Beli Kuat": return "bg-green-600 text-white";
    case "Beli": return "bg-green-100 text-green-800";
    case "Tahan": return "bg-yellow-100 text-yellow-800";
    case "Jual": return "bg-red-100 text-red-800";
    default: return "bg-gray-100 text-gray-600";
  }
}

interface ProgressBarProps {
  label: string;
  value: number | null;
}

function ProgressBar({ label, value }: ProgressBarProps) {
  const pct = value !== null ? Math.min(100, Math.max(0, value)) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-gray-600">
        <span>{label}</span>
        <span>{value !== null ? `${value.toFixed(0)}/100` : "N/A"}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ScoreCard({ score }: ScoreCardProps) {
  const category = getCategory(score.score);

  // score_factors from backend is an object {valuation, quality, momentum}, not string[]
  // Extract available factor labels for display
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
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
        Skor Saham
      </h2>

      {/* Score circle */}
      <div className="mb-4 flex items-center gap-4">
        <div
          className={`flex h-20 w-20 shrink-0 items-center justify-center rounded-full ring-4 ${category.ring} ${category.bg}`}
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
          <p className="mb-2 text-xs font-medium text-gray-500">Faktor Pendukung</p>
          <ul className="space-y-1">
            {factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                <span className="mt-0.5 text-green-500">✓</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-[10px] leading-relaxed text-gray-400">
        * Skor bersifat informatif dan bukan merupakan rekomendasi investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab investor.
      </p>
    </div>
  );
}
