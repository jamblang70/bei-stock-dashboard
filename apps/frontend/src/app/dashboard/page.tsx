"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { PaginatedResponse, RankingItem } from "@/types";
import RankingTable from "@/components/ranking/RankingTable";
import SectorFilter from "@/components/ranking/SectorFilter";
import SearchBar from "@/components/search/SearchBar";
import Spinner from "@/components/ui/Spinner";

const PER_PAGE = 25;

export default function DashboardPage() {
  const [data, setData] = useState<RankingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sector, setSector] = useState("");
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

      const res = await apiGet<PaginatedResponse<RankingItem>>(
        `/ranking/?${params.toString()}`
      );
      console.log("Ranking response:", res);
      setData(res.data ?? res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      console.error("Ranking fetch error:", err);
      setError("Gagal memuat data ranking. Silakan coba lagi.");
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, sector, sortBy, sortOrder]);

  useEffect(() => {
    fetchRanking();
  }, [fetchRanking]);

  function handleSort(col: string) {
    if (sortBy === col) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setPage(1);
  }

  function handleSectorChange(val: string) {
    setSector(val);
    setPage(1);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              BEI Stock Dashboard
            </h1>
            <p className="text-sm text-gray-500">Ranking Saham Terbaik</p>
          </div>
          <SearchBar />
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-4">
          <SectorFilter value={sector} onChange={handleSectorChange} />
          {sector && (
            <button
              onClick={() => handleSectorChange("")}
              className="text-sm text-blue-600 hover:underline"
            >
              Reset filter
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : (
          <RankingTable
            data={data}
            total={total}
            page={page}
            perPage={PER_PAGE}
            onPageChange={setPage}
            onSort={handleSort}
            sortBy={sortBy}
            sortOrder={sortOrder}
          />
        )}
      </main>
    </div>
  );
}
