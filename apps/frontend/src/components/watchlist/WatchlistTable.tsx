"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiDelete } from "@/lib/api";
import type { WatchlistItem } from "@/types";

interface WatchlistTableProps {
  items: WatchlistItem[];
  token: string;
  onItemsChange: (items: WatchlistItem[]) => void;
}

function formatPrice(val: number | null): string {
  if (val === null || val === undefined) return "-";
  return new Intl.NumberFormat("id-ID").format(val);
}

function formatNumber(val: number | null, decimals = 2): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(decimals);
}

function RecommendationBadge({ rec }: { rec: string | null | undefined }) {
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

export default function WatchlistTable({
  items,
  token,
  onItemsChange,
}: WatchlistTableProps) {
  const router = useRouter();
  const [deletingCodes, setDeletingCodes] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function handleDelete(code: string) {
    // Optimistic update
    const previous = [...items];
    onItemsChange(items.filter((i) => (i.code ?? i.stock?.code) !== code));
    setDeletingCodes((prev) => new Set(prev).add(code));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[code];
      return next;
    });

    try {
      await apiDelete(`/watchlist/${code}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Rollback on error
      onItemsChange(previous);
      setErrors((prev) => ({
        ...prev,
        [code]: "Gagal menghapus. Coba lagi.",
      }));
    } finally {
      setDeletingCodes((prev) => {
        const next = new Set(prev);
        next.delete(code);
        return next;
      });
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {[
                "Kode",
                "Nama",
                "Sektor",
                "Harga",
                "Perubahan%",
                "Skor",
                "Rekomendasi",
                "Aksi",
              ].map((h) => (
                <th
                  key={h}
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {items.map((item) => {
              const code = item.code ?? item.stock?.code ?? "";
              const name = item.name ?? item.stock?.name ?? "";
              const sector = item.sector ?? item.stock?.sector ?? null;
              const price = item.price ?? item.last_price ?? null;
              const changePct = item.change_pct;
              const scoreVal = typeof item.score === "number" ? item.score : (item.score as any)?.score ?? null;
              const rec = item.recommendation ?? (item.score as any)?.recommendation ?? null;
              const changeColor =
                changePct === null
                  ? "text-gray-500"
                  : changePct > 0
                    ? "text-green-600"
                    : changePct < 0
                      ? "text-red-600"
                      : "text-gray-500";

              return (
                <tr key={code}>
                  <td
                    className="cursor-pointer px-4 py-3 font-semibold text-blue-700 hover:underline"
                    onClick={() => router.push(`/stock/${code}`)}
                  >
                    {code}
                  </td>
                  <td
                    className="max-w-[180px] cursor-pointer truncate px-4 py-3 text-gray-900 hover:underline"
                    onClick={() => router.push(`/stock/${code}`)}
                  >
                    {name}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {sector ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-900">
                    {formatPrice(price)}
                  </td>
                  <td className={`px-4 py-3 text-right font-medium ${changeColor}`}>
                    {changePct !== null
                      ? `${changePct > 0 ? "+" : ""}${formatNumber(changePct)}%`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">
                    {scoreVal !== null ? formatNumber(scoreVal, 1) : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <RecommendationBadge rec={rec} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col items-start gap-1">
                      <button
                        onClick={() => handleDelete(code)}
                        disabled={deletingCodes.has(code)}
                        className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                        aria-label={`Hapus ${code} dari watchlist`}
                      >
                        {deletingCodes.has(code) ? "Menghapus..." : "Hapus"}
                      </button>
                      {errors[code] && (
                        <span className="text-xs text-red-500">
                          {errors[code]}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
