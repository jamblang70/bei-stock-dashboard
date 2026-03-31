"use client";

import { useRouter } from "next/navigation";
import type { RankingItem } from "@/types";

type SortOrder = "asc" | "desc";

interface RankingTableProps {
  data: RankingItem[];
  total: number;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onSort: (sortBy: string) => void;
  sortBy: string;
  sortOrder: SortOrder;
}

const COLUMNS: { key: string; label: string; sortable: boolean }[] = [
  { key: "no", label: "No", sortable: false },
  { key: "code", label: "Kode", sortable: true },
  { key: "name", label: "Nama", sortable: true },
  { key: "sector", label: "Sektor", sortable: true },
  { key: "last_price", label: "Harga", sortable: true },
  { key: "change_pct", label: "Perubahan%", sortable: true },
  { key: "score", label: "Skor", sortable: true },
  { key: "recommendation", label: "Rekomendasi", sortable: false },
  { key: "per", label: "PER", sortable: true },
  { key: "pbv", label: "PBV", sortable: true },
  { key: "roe", label: "ROE", sortable: true },
  { key: "dividend_yield", label: "Div.Yield", sortable: true },
];

function formatNumber(val: number | null, decimals = 2): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(decimals);
}

function formatPrice(val: number | null): string {
  if (val === null || val === undefined) return "-";
  return new Intl.NumberFormat("id-ID").format(val);
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) return <span className="text-text-muted">-</span>;
  const s = Number(score);
  let bg = "bg-red-500/20 text-red-400";
  if (s >= 80) bg = "bg-emerald-500/20 text-emerald-400";
  else if (s >= 60) bg = "bg-blue-500/20 text-blue-400";
  else if (s >= 40) bg = "bg-yellow-500/20 text-yellow-400";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${bg}`}>
      {s.toFixed(1)}
    </span>
  );
}

function RecommendationBadge({ rec }: { rec: string | null }) {
  if (!rec) return <span className="text-text-muted">-</span>;
  const colors: Record<string, string> = {
    "Beli Kuat": "bg-emerald-500/20 text-emerald-400",
    Beli: "bg-blue-500/20 text-blue-400",
    Tahan: "bg-yellow-500/20 text-yellow-400",
    Jual: "bg-red-500/20 text-red-400",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[rec] ?? "bg-gray-500/20 text-gray-400"}`}
    >
      {rec}
    </span>
  );
}

export default function RankingTable({
  data,
  total,
  page,
  perPage,
  onPageChange,
  onSort,
  sortBy,
  sortOrder,
}: RankingTableProps) {
  const router = useRouter();
  const totalPages = Math.ceil(total / perPage);
  const startNo = (page - 1) * perPage + 1;

  function SortIcon({ col }: { col: string }) {
    if (sortBy !== col) {
      return <span className="ml-1 text-text-muted">↕</span>;
    }
    return (
      <span className="ml-1 text-emerald-400">
        {sortOrder === "asc" ? "↑" : "↓"}
      </span>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-dark-border bg-dark-surface">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-dark-border text-sm">
          <thead className="bg-dark-bg/50">
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary ${
                    col.sortable
                      ? "cursor-pointer select-none hover:text-text-primary transition-colors"
                      : ""
                  }`}
                  onClick={col.sortable ? () => onSort(col.key) : undefined}
                >
                  {col.label}
                  {col.sortable && <SortIcon col={col.key} />}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border/50">
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  className="py-10 text-center text-text-muted"
                >
                  Tidak ada data
                </td>
              </tr>
            ) : (
              data.map((item, idx) => {
                const changePct = item.change_pct;
                const changeColor =
                  changePct === null
                    ? "text-text-muted"
                    : changePct > 0
                      ? "text-emerald-400"
                      : changePct < 0
                        ? "text-red-400"
                        : "text-text-muted";

                return (
                  <tr
                    key={item.code}
                    className="cursor-pointer transition-colors hover:bg-dark-hover"
                    onClick={() => router.push(`/stock/${item.code}`)}
                  >
                    <td className="px-4 py-3 text-text-muted">
                      {startNo + idx}
                    </td>
                    <td className="px-4 py-3 font-semibold text-emerald-400">
                      {item.code}
                    </td>
                    <td className="max-w-[180px] truncate px-4 py-3 text-text-primary">
                      {item.name}
                    </td>
                    <td className="px-4 py-3 text-text-secondary">
                      {item.sector ?? "-"}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-text-primary">
                      {formatPrice(item.last_price)}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${changeColor}`}>
                      {changePct !== null
                        ? `${changePct > 0 ? "+" : ""}${formatNumber(changePct)}%`
                        : "-"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <ScoreBadge score={item.score} />
                    </td>
                    <td className="px-4 py-3">
                      <RecommendationBadge rec={item.recommendation} />
                    </td>
                    <td className="px-4 py-3 text-right text-text-secondary">
                      {formatNumber(item.per)}
                    </td>
                    <td className="px-4 py-3 text-right text-text-secondary">
                      {formatNumber(item.pbv)}
                    </td>
                    <td className="px-4 py-3 text-right text-text-secondary">
                      {item.roe !== null ? `${formatNumber(item.roe)}%` : "-"}
                    </td>
                    <td className="px-4 py-3 text-right text-text-secondary">
                      {item.dividend_yield !== null
                        ? `${formatNumber(item.dividend_yield)}%`
                        : "-"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between border-t border-dark-border bg-dark-bg/50 px-4 py-3">
        <p className="text-sm text-text-secondary">
          {total > 0
            ? `Menampilkan ${startNo}–${Math.min(startNo + perPage - 1, total)} dari ${total} saham`
            : "Tidak ada data"}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-md border border-dark-border bg-dark-surface px-3 py-1.5 text-sm font-medium text-text-secondary hover:bg-dark-hover hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
          >
            ← Prev
          </button>
          <span className="text-sm text-text-secondary">
            {page} / {totalPages || 1}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-md border border-dark-border bg-dark-surface px-3 py-1.5 text-sm font-medium text-text-secondary hover:bg-dark-hover hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
