"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";

interface TodayStockItem {
  code: string;
  name: string;
  sector: string | null;
  last_price: number | null;
  change_pct: number | null;
  volume: number | null;
}

interface TodayResponse {
  top_gainers: TodayStockItem[];
  top_losers: TodayStockItem[];
  most_active: TodayStockItem[];
}

function fmt(val: number | null, d = 2): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(d);
}

function fmtPrice(val: number | null): string {
  if (val === null || val === undefined) return "-";
  return new Intl.NumberFormat("id-ID").format(val);
}

function fmtVolume(val: number | null): string {
  if (val === null || val === undefined) return "-";
  if (val >= 1_000_000_000) return `${(val / 1_000_000_000).toFixed(1)}B`;
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
  return val.toString();
}

function StockCard({
  item,
  theme,
}: {
  item: TodayStockItem;
  theme: "green" | "red" | "blue";
}) {
  const borderColor =
    theme === "green"
      ? "border-emerald-500/30"
      : theme === "red"
        ? "border-red-500/30"
        : "border-blue-500/30";
  const accentColor =
    theme === "green"
      ? "text-emerald-400"
      : theme === "red"
        ? "text-red-400"
        : "text-blue-400";

  const pct = item.change_pct;
  const changeColor =
    pct !== null && pct > 0
      ? "text-emerald-400"
      : pct !== null && pct < 0
        ? "text-red-400"
        : "text-text-muted";

  return (
    <Link href={`/stock/${item.code}`}>
      <div
        className={`rounded-xl border ${borderColor} bg-dark-surface p-4 hover:bg-dark-hover transition-colors cursor-pointer`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className={`font-bold ${accentColor}`}>{item.code}</p>
            <p className="truncate text-sm text-text-secondary">{item.name}</p>
            {item.sector && (
              <p className="text-[10px] text-text-muted mt-0.5">{item.sector}</p>
            )}
          </div>
          <div className="text-right shrink-0">
            <p className="font-semibold text-text-primary">{fmtPrice(item.last_price)}</p>
            <p className={`text-xs font-medium ${changeColor}`}>
              {pct !== null ? `${pct > 0 ? "+" : ""}${fmt(pct)}%` : "-"}
            </p>
          </div>
        </div>
        <div className="mt-2 text-xs text-text-muted">
          Vol: {fmtVolume(item.volume)}
        </div>
      </div>
    </Link>
  );
}

function Section({
  title,
  items,
  theme,
  icon,
}: {
  title: string;
  items: TodayStockItem[];
  theme: "green" | "red" | "blue";
  icon: string;
}) {
  const headerColor =
    theme === "green"
      ? "text-emerald-400"
      : theme === "red"
        ? "text-red-400"
        : "text-blue-400";

  return (
    <div>
      <h2 className={`text-lg font-bold ${headerColor} mb-3 flex items-center gap-2`}>
        <span>{icon}</span> {title}
      </h2>
      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">Tidak ada data</p>
        ) : (
          items.map((item) => (
            <StockCard key={item.code} item={item} theme={theme} />
          ))
        )}
      </div>
    </div>
  );
}

export default function TodayPage() {
  const [data, setData] = useState<TodayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet<TodayResponse>("/stocks/today");
        setData(res);
      } catch {
        setError("Gagal memuat data saham hari ini.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-dark-bg">
      <header className="sticky top-0 z-30 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-lg font-bold text-text-primary sm:text-xl">
                Saham Hari Ini
              </h1>
              <p className="text-xs text-text-secondary sm:text-sm">
                Top Gainers, Losers & Most Active
              </p>
            </div>
            <nav className="flex items-center gap-3 text-sm">
              <Link href="/dashboard" className="text-text-secondary hover:text-emerald-400 transition-colors">
                Dashboard
              </Link>
              <span className="text-emerald-400 font-medium">Saham Hari Ini</span>
              <Link href="/compare" className="text-text-secondary hover:text-emerald-400 transition-colors">
                Bandingkan
              </Link>
              <Link href="/dividends" className="text-text-secondary hover:text-emerald-400 transition-colors">
                Dividen
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : data ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Section title="Top Gainers" items={data.top_gainers} theme="green" icon="📈" />
            <Section title="Top Losers" items={data.top_losers} theme="red" icon="📉" />
            <Section title="Most Active" items={data.most_active} theme="blue" icon="🔥" />
          </div>
        ) : null}
      </main>
    </div>
  );
}
