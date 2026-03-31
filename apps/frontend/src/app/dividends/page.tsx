"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import SyariahFilter from "@/components/ranking/SyariahFilter";
import Spinner from "@/components/ui/Spinner";

interface DividendStockItem {
  code: string;
  name: string;
  sector: string | null;
  last_price: number | null;
  dividend_yield: number | null;
  dividend_per_share: number | null;
  annual_dividend_estimate: number | null;
  per: number | null;
  score: number | null;
  is_syariah: boolean;
}

interface DividendResponse {
  data: DividendStockItem[];
  total: number;
}

function fmt(val: number | null, d = 2): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(d);
}

function fmtPrice(val: number | null): string {
  if (val === null || val === undefined) return "-";
  return new Intl.NumberFormat("id-ID").format(val);
}

function yieldColor(y: number | null): string {
  if (y === null) return "text-text-muted";
  if (y > 5) return "text-emerald-400";
  if (y >= 2) return "text-yellow-400";
  return "text-text-muted";
}

function scoreBg(score: number | null): string {
  if (score === null) return "bg-dark-bg text-text-muted";
  if (score >= 80) return "bg-emerald-500/20 text-emerald-400";
  if (score >= 60) return "bg-blue-500/20 text-blue-400";
  if (score >= 40) return "bg-yellow-500/20 text-yellow-400";
  return "bg-red-500/20 text-red-400";
}

function MobileDividendCard({ item, rank }: { item: DividendStockItem; rank: number }) {
  const router = useRouter();
  return (
    <div
      onClick={() => router.push(`/stock/${item.code}`)}
      className="rounded-xl border border-dark-border bg-dark-surface p-4 active:bg-dark-hover transition-colors cursor-pointer"
    >
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
            </div>
            <p className="truncate text-sm text-text-secondary">{item.name}</p>
            {item.sector && <p className="text-[10px] text-text-muted mt-0.5">{item.sector}</p>}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="font-semibold text-text-primary">{fmtPrice(item.last_price)}</p>
          <p className={`text-sm font-bold ${yieldColor(item.dividend_yield)}`}>
            {item.dividend_yield !== null ? `${fmt(item.dividend_yield, 1)}%` : "-"}
          </p>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        {item.score !== null && (
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${scoreBg(item.score)}`}>
            Skor {fmt(item.score, 1)}
          </span>
        )}
        <div className="ml-auto flex gap-3 text-[10px] text-text-muted">
          {item.dividend_per_share !== null && <span>Div/Share Rp{fmtPrice(item.dividend_per_share)}</span>}
          {item.per !== null && <span>PER {fmt(item.per)}</span>}
        </div>
      </div>
    </div>
  );
}

const PER_PAGE = 25;

export default function DividendsPage() {
  const router = useRouter();
  const [data, setData] = useState<DividendStockItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [syariah, setSyariah] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Summary stats
  const [avgYield, setAvgYield] = useState<number | null>(null);
  const [highestStock, setHighestStock] = useState<{ code: string; yield: number } | null>(null);
  const [totalDividendStocks, setTotalDividendStocks] = useState(0);

  const fetchDividends = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(page),
        per_page: String(PER_PAGE),
      });
      if (syariah) params.set("syariah", "true");
      const res = await apiGet<DividendResponse>(`/stocks/dividends?${params.toString()}`);
      setData(res.data ?? []);
      setTotal(res.total ?? 0);

      // Compute summary from first page when on page 1
      if (page === 1 && res.data.length > 0) {
        const yields = res.data.filter((d) => d.dividend_yield !== null).map((d) => d.dividend_yield!);
        setAvgYield(yields.length > 0 ? yields.reduce((a, b) => a + b, 0) / yields.length : null);
        setHighestStock({ code: res.data[0].code, yield: res.data[0].dividend_yield ?? 0 });
        setTotalDividendStocks(res.total);
      }
    } catch {
      setError("Gagal memuat data dividen.");
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, syariah]);

  useEffect(() => { fetchDividends(); }, [fetchDividends]);

  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div className="min-h-screen bg-dark-bg">
      <header className="sticky top-0 z-30 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-lg font-bold text-text-primary sm:text-xl">Dividend Tracker</h1>
              <p className="text-xs text-text-secondary sm:text-sm">Saham dengan Dividen Tertinggi</p>
            </div>
            <nav className="flex items-center gap-3 text-sm">
              <Link href="/dashboard" className="text-text-secondary hover:text-emerald-400 transition-colors">Dashboard</Link>
              <Link href="/today" className="text-text-secondary hover:text-emerald-400 transition-colors">Saham Hari Ini</Link>
              <Link href="/compare" className="text-text-secondary hover:text-emerald-400 transition-colors">Bandingkan</Link>
              <span className="text-emerald-400 font-medium">Dividen</span>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="rounded-xl border border-dark-border bg-dark-surface p-4">
            <p className="text-xs text-text-muted mb-1">Rata-rata Yield</p>
            <p className="text-2xl font-bold text-emerald-400">{avgYield !== null ? `${fmt(avgYield, 1)}%` : "-"}</p>
          </div>
          <div className="rounded-xl border border-dark-border bg-dark-surface p-4">
            <p className="text-xs text-text-muted mb-1">Tertinggi</p>
            <p className="text-2xl font-bold text-yellow-400">
              {highestStock ? `${highestStock.code} — ${fmt(highestStock.yield, 1)}%` : "-"}
            </p>
          </div>
          <div className="rounded-xl border border-dark-border bg-dark-surface p-4">
            <p className="text-xs text-text-muted mb-1">Total Saham Dividen</p>
            <p className="text-2xl font-bold text-text-primary">{totalDividendStocks}</p>
          </div>
        </div>

        {/* Filter */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SyariahFilter value={syariah} onChange={(v) => { setSyariah(v); setPage(1); }} />
          {syariah && (
            <button onClick={() => { setSyariah(false); setPage(1); }} className="text-xs text-emerald-400 hover:text-emerald-300">
              Reset Syariah
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20"><Spinner size="lg" /></div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden md:block rounded-xl border border-dark-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-dark-surface border-b border-dark-border">
                    <th className="text-left px-4 py-3 text-text-muted font-medium w-10">No</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">Kode</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">Nama</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">Sektor</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">Harga</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">Div. Yield (%)</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">Div/Share (Rp)</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">PER</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">Skor</th>
                    <th className="text-center px-4 py-3 text-text-muted font-medium">Syariah</th>
                  </tr>
                </thead>
                <tbody>
                  {data.length === 0 ? (
                    <tr><td colSpan={10} className="py-10 text-center text-text-muted">Tidak ada data</td></tr>
                  ) : (
                    data.map((item, idx) => (
                      <tr
                        key={item.code}
                        onClick={() => router.push(`/stock/${item.code}`)}
                        className={`border-b border-dark-border cursor-pointer hover:bg-dark-hover transition-colors ${idx % 2 === 0 ? "bg-dark-bg" : "bg-dark-surface"}`}
                      >
                        <td className="px-4 py-3 text-text-muted">{(page - 1) * PER_PAGE + idx + 1}</td>
                        <td className="px-4 py-3 font-bold text-emerald-400">{item.code}</td>
                        <td className="px-4 py-3 text-text-secondary max-w-[200px] truncate">{item.name}</td>
                        <td className="px-4 py-3 text-text-muted text-xs">{item.sector ?? "-"}</td>
                        <td className="px-4 py-3 text-right text-text-primary font-medium">{fmtPrice(item.last_price)}</td>
                        <td className={`px-4 py-3 text-right font-bold ${yieldColor(item.dividend_yield)}`}>
                          {item.dividend_yield !== null ? fmt(item.dividend_yield, 1) : "-"}
                        </td>
                        <td className="px-4 py-3 text-right text-text-secondary">{item.dividend_per_share !== null ? fmtPrice(item.dividend_per_share) : "-"}</td>
                        <td className="px-4 py-3 text-right text-text-secondary">{item.per !== null ? fmt(item.per) : "-"}</td>
                        <td className="px-4 py-3 text-right">
                          {item.score !== null ? (
                            <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${scoreBg(item.score)}`}>
                              {fmt(item.score, 1)}
                            </span>
                          ) : "-"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {item.is_syariah ? (
                            <span className="rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-400">Syariah</span>
                          ) : <span className="text-text-muted">-</span>}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden space-y-3">
              {data.length === 0 ? (
                <p className="py-10 text-center text-text-muted">Tidak ada data</p>
              ) : (
                data.map((item, idx) => (
                  <MobileDividendCard key={item.code} item={item} rank={(page - 1) * PER_PAGE + idx + 1} />
                ))
              )}
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-text-secondary sm:text-sm">
                {total > 0 ? `${(page - 1) * PER_PAGE + 1}–${Math.min(page * PER_PAGE, total)} dari ${total}` : ""}
              </p>
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(page - 1)} disabled={page <= 1}
                  className="rounded-lg border border-dark-border bg-dark-surface px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-dark-hover disabled:opacity-40 transition-colors">
                  ←
                </button>
                <span className="text-xs text-text-secondary">{page}/{totalPages || 1}</span>
                <button onClick={() => setPage(page + 1)} disabled={page >= totalPages}
                  className="rounded-lg border border-dark-border bg-dark-surface px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-dark-hover disabled:opacity-40 transition-colors">
                  →
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
