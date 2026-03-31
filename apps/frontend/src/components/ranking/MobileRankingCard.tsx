"use client";

import { useRouter } from "next/navigation";
import type { RankingItem } from "@/types";

interface Props {
  item: RankingItem;
  rank: number;
}

function fmt(val: number | null, d = 2): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(d);
}

export default function MobileRankingCard({ item, rank }: Props) {
  const router = useRouter();
  const pct = item.change_pct;
  const isUp = pct !== null && pct > 0;
  const isDown = pct !== null && pct < 0;
  const changeColor = isUp ? "text-emerald-400" : isDown ? "text-red-400" : "text-text-muted";
  const changeBg = isUp ? "bg-emerald-500/10" : isDown ? "bg-red-500/10" : "bg-dark-bg";

  const score = item.score;
  let scoreBg = "bg-red-500/20 text-red-400";
  if (score !== null) {
    if (score >= 80) scoreBg = "bg-emerald-500/20 text-emerald-400";
    else if (score >= 60) scoreBg = "bg-blue-500/20 text-blue-400";
    else if (score >= 40) scoreBg = "bg-yellow-500/20 text-yellow-400";
  }

  const recColors: Record<string, string> = {
    "Beli Kuat": "text-emerald-400",
    Beli: "text-blue-400",
    Tahan: "text-yellow-400",
    Jual: "text-red-400",
  };

  return (
    <div
      onClick={() => router.push(`/stock/${item.code}`)}
      className="rounded-xl border border-dark-border bg-dark-surface p-4 active:bg-dark-hover transition-colors cursor-pointer"
    >
      {/* Top row: rank + code + name + price */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-dark-bg text-xs font-bold text-text-muted">
            {rank}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-bold text-emerald-400">{item.code}</span>
              {item.is_syariah && (
                <span className="rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-400">
                  Syariah
                </span>
              )}
              {item.sector && (
                <span className="truncate text-[10px] text-text-muted">{item.sector}</span>
              )}
            </div>
            <p className="truncate text-sm text-text-secondary">{item.name}</p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="font-semibold text-text-primary">
            {item.last_price !== null ? new Intl.NumberFormat("id-ID").format(item.last_price) : "-"}
          </p>
          <p className={`text-xs font-medium ${changeColor}`}>
            {pct !== null ? `${isUp ? "+" : ""}${fmt(pct)}%` : "-"}
          </p>
        </div>
      </div>

      {/* Bottom row: score + recommendation + metrics */}
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        {score !== null && (
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${scoreBg}`}>
            Skor {fmt(score, 1)}
          </span>
        )}
        {item.recommendation && (
          <span className={`text-xs font-medium ${recColors[item.recommendation] ?? "text-text-muted"}`}>
            {item.recommendation}
          </span>
        )}
        <div className="ml-auto flex gap-3 text-[10px] text-text-muted">
          {item.per !== null && <span>PER {fmt(item.per)}</span>}
          {item.pbv !== null && <span>PBV {fmt(item.pbv)}</span>}
          {item.roe !== null && <span>ROE {fmt(item.roe)}%</span>}
        </div>
      </div>
    </div>
  );
}
