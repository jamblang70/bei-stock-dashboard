"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { PaginatedResponse, RankingItem } from "@/types";
import RankingTable from "@/components/ranking/RankingTable";
import MobileRankingCard from "@/components/ranking/MobileRankingCard";
import SectorFilter from "@/components/ranking/SectorFilter";
import SyariahFilter from "@/components/ranking/SyariahFilter";
import SearchBar from "@/components/search/SearchBar";
import Spinner from "@/components/ui/Spinner";

const PER_PAGE = 25;

export default function DashboardPage() {
  const [data, setData] = useState<RankingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sector, setSector] = useState("");
  const [syariah, setSyariah] = useState(false);
  const [sortBy, setSortBy] = useState("score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRanking = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(page),
        per_page: String(PER_PAGE),
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      if (sector) params.set("sector", sector);
      if (syariah) params.set("syariah", "true");
      const res = await apiGet<PaginatedResponse<RankingItem>>(
        `/ranking/?${params.toString()}`
      );
      setData(res.data ?? res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      console.error("Ranking fetch error:", err);
      setError("Gagal memuat data ranking.");
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, sector, syariah, sortBy, sortOrder]);

  useEffect(() => { fetchRanking(); }, [fetchRanking]);

  function handleSort(col: string) {
    if (sortBy === col) setSortOrder((p) => (p === "asc" ? "desc" : "asc"));
    else { setSortBy(col); setSortOrder("desc"); }
    setPage(1);
  }

  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-bold text-text-primary sm:text-xl">
                  BEI Stock Dashboard
                </h1>
                <p className="text-xs text-text-secondary sm:text-sm">Ranking Saham Terbaik</p>
              </div>
              <nav className="flex items-center gap-3 text-sm ml-4">
                <span className="text-emerald-400 font-medium">Dashboard</span>
                <Link href="/today" className="text-text-secondary hover:text-emerald-400 transition-colors">
                  Saham Hari Ini
                </Link>
                <Link href="/compare" className="text-text-secondary hover:text-emerald-400 transition-colors">
                  Bandingkan
                </Link>
                <Link href="/dividends" className="text-text-secondary hover:text-emerald-400 transition-colors">
                  Dividen
                </Link>
              </nav>
            </div>
            <SearchBar />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        {/* Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SectorFilter value={sector} onChange={(v) => { setSector(v); setPage(1); }} />
          <SyariahFilter value={syariah} onChange={(v) => { setSyariah(v); setPage(1); }} />
          {sector && (
            <button onClick={() => { setSector(""); setPage(1); }} className="text-xs text-emerald-400 hover:text-emerald-300">
              Reset
            </button>
          )}
          {syariah && (
            <button onClick={() => { setSyariah(false); setPage(1); }} className="text-xs text-emerald-400 hover:text-emerald-300">
              Reset Syariah
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20"><Spinner size="lg" /></div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block">
              <RankingTable data={data} total={total} page={page} perPage={PER_PAGE}
                onPageChange={setPage} onSort={handleSort} sortBy={sortBy} sortOrder={sortOrder} />
            </div>

            {/* Mobile cards */}
            <div className="md:hidden space-y-3">
              {data.length === 0 ? (
                <p className="py-10 text-center text-text-muted">Tidak ada data</p>
              ) : (
                data.map((item, idx) => (
                  <MobileRankingCard key={item.code} item={item} rank={(page - 1) * PER_PAGE + idx + 1} />
                ))
              )}
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-text-secondary sm:text-sm">
                {total > 0 ? `${(page-1)*PER_PAGE+1}–${Math.min(page*PER_PAGE, total)} dari ${total}` : ""}
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
