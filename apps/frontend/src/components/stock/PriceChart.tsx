"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { apiGet } from "@/lib/api";
import type { PriceHistory } from "@/types";

type Range = "1w" | "1m" | "3m" | "6m" | "1y" | "5y";

const RANGES: { label: string; value: Range }[] = [
  { label: "1M", value: "1w" },
  { label: "1B", value: "1m" },
  { label: "3B", value: "3m" },
  { label: "6B", value: "6m" },
  { label: "1T", value: "1y" },
  { label: "5T", value: "5y" },
];

function formatDate(dateStr: string, range: Range): string {
  const date = new Date(dateStr);
  if (range === "1w" || range === "1m") {
    return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" });
  }
  if (range === "3m" || range === "6m") {
    return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" });
  }
  return date.toLocaleDateString("id-ID", { month: "short", year: "2-digit" });
}

function formatPrice(value: number): string {
  return `Rp ${value.toLocaleString("id-ID")}`;
}

interface PriceChartProps {
  code: string;
}

export default function PriceChart({ code }: PriceChartProps) {
  const [range, setRange] = useState<Range>("3m");
  const [data, setData] = useState<PriceHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    apiGet<PriceHistory[]>(`/stocks/${code}/price-history?range=${range}`)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code, range]);

  const chartData = data.map((d) => ({
    date: d.date,
    close: d.close,
    label: formatDate(d.date, range),
  }));

  const prices = chartData.map((d) => d.close);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 0;
  const isPositive =
    chartData.length >= 2
      ? chartData[chartData.length - 1].close >= chartData[0].close
      : true;

  const strokeColor = isPositive ? "#16a34a" : "#dc2626";
  const fillColor = isPositive ? "#dcfce7" : "#fee2e2";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Grafik Harga
        </h2>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setRange(r.value)}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                range === r.value
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            Gagal memuat data harga
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            Data tidak tersedia
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={fillColor} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={fillColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[minPrice * 0.98, maxPrice * 1.02]}
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
                width={40}
              />
              <Tooltip
                formatter={(value: number) => [formatPrice(value), "Harga"]}
                labelFormatter={(label: string) => `Tanggal: ${label}`}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={strokeColor}
                strokeWidth={2}
                fill="url(#priceGradient)"
                dot={false}
                activeDot={{ r: 4 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
