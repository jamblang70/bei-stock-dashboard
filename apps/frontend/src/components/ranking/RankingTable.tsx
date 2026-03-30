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

function RecommendationBadge({ rec }: { rec: string | null }) {
  if (!rec) return <span className="text-gray-400">-</span>;
  const colors: Record<string, string> = {
    "Beli Kuat": "bg-green-100 text-green-800",
    Beli: "bg-blue-100 text-blue-800",
    Tahan: "bg-yellow-100 text-yellow-800",
    Jual: "bg-red-100 text-red-800",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[rec] ?? "bg-gray-100 text-gray-800"}`}
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
      return <span className="ml-1 text-gray-300">↕</span>;
    }
    return (
      <span className="ml-1 text-blue-600">
        {sortOrder === "asc" ? "↑" : "↓"}
      </span>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 ${
                    col.sortable
                      ? "cursor-pointer select-none hover:bg-gray-100"
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
          <tbody className="divide-y divide-gray-100 bg-white">
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  className="py-10 text-center text-gray-400"
                >
                  Tidak ada data
                </td>
              </tr>
            ) : (
              data.map((item, idx) => {
                const changePct = item.change_pct;
                const changeColor =
                  changePct === null
                    ? "text-gray-500"
                    : changePct > 0
                      ? "text-green-600"
                      : changePct < 0
                        ? "text-red-600"
                        : "text-gray-500";

                return (
                  <tr
                    key={item.code}
                    className="cursor-pointer transition-colors hover:bg-blue-50"
                    onClick={() => router.push(`/stock/${item.code}`)}
                  >
                    <td className="px-4 py-3 text-gray-400">
                      {startNo + idx}
                    </td>
                    <td className="px-4 py-3 font-semibold text-blue-700">
                      {item.code}
                    </td>
                    <td className="max-w-[180px] truncate px-4 py-3 text-gray-900">
                      {item.name}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {item.sector ?? "-"}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {formatPrice(item.last_price)}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${changeColor}`}>
                      {changePct !== null
                        ? `${changePct > 0 ? "+" : ""}${formatNumber(changePct)}%`
                        : "-"}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">
                      {formatNumber(item.score, 1)}
                    </td>
                    <td className="px-4 py-3">
                      <RecommendationBadge rec={item.recommendation} />
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {formatNumber(item.per)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {formatNumber(item.pbv)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {item.roe !== null ? `${formatNumber(item.roe)}%` : "-"}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
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
      <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-3">
        <p className="text-sm text-gray-500">
          {total > 0
            ? `Menampilkan ${startNo}–${Math.min(startNo + perPage - 1, total)} dari ${total} saham`
            : "Tidak ada data"}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="text-sm text-gray-600">
            {page} / {totalPages || 1}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
