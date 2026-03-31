"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import type { Stock } from "@/types";

interface CompareStockItem {
  code: string;
  name: string;
  sector: string | null;
  last_price: number | null;
  change_pct: number | null;
  per: number | null;
  pbv: number | null;
  roe: number | null;
  roa: number | null;
  net_profit_margin: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  dividend_yield: number | null;
  eps: number | null;
  beta: number | null;
  score: number | null;
  recommendation: string | null;
}

interface CompareResponse {
  stocks: CompareStockItem[];
}

// Stock selector with search
function StockSelector({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (code: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Stock[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const data = await apiGet<Stock[]>(
          `/stocks/search?q=${encodeURIComponent(query)}`
        );
        setResults(data);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative flex-1 min-w-0">
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type="text"
        value={value || query}
        onChange={(e) => {
          setQuery(e.target.value);
          if (value) onChange("");
        }}
        onFocus={() => query.trim() && setOpen(true)}
        placeholder="Cari kode saham..."
        className="w-full rounded-lg border border-dark-border bg-dark-bg py-2 px-3 text-sm text-text-primary placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors"
      />
      {open && results.length > 0 && (
        <div className="absolute z-20 mt-1 w-full rounded-lg border border-dark-border bg-dark-surface shadow-lg max-h-48 overflow-y-auto">
          {results.map((s) => (
            <button
              key={s.code}
              onClick={() => {
                onChange(s.code);
                setQuery(s.code);
                setOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-dark-hover transition-colors"
            >
              <span className="font-bold text-emerald-400">{s.code}</span>
              <span className="text-text-secondary ml-2">{s.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

type MetricDef = {
  label: string;
  key: keyof CompareStockItem;
  format?: (v: number | null) => string;
  higherBetter?: boolean;
  lowerBetter?: boolean;
};

const METRICS: MetricDef[] = [
  {
    label: "Harga",
    key: "last_price",
    format: (v) =>
      v !== null ? new Intl.NumberFormat("id-ID").format(v) : "-",
  },
  { label: "PER", key: "per", lowerBetter: true },
  { label: "PBV", key: "pbv", lowerBetter: true },
  { label: "ROE (%)", key: "roe", higherBetter: true },
  { label: "ROA (%)", key: "roa", higherBetter: true },
  { label: "Net Margin (%)", key: "net_profit_margin", higherBetter: true },
  { label: "DER", key: "debt_to_equity", lowerBetter: true },
  { label: "Current Ratio", key: "current_ratio", higherBetter: true },
  { label: "Div Yield (%)", key: "dividend_yield", higherBetter: true },
  { label: "EPS", key: "eps", higherBetter: true },
  { label: "Beta", key: "beta" },
  { label: "Skor", key: "score", higherBetter: true },
  {
    label: "Rekomendasi",
    key: "recommendation",
    format: (v) => (v !== null ? String(v) : "-"),
  },
];

function fmtVal(v: unknown): string {
  if (v === null || v === undefined) return "-";
  if (typeof v === "number") return v.toFixed(2);
  return String(v);
}

function cellColor(
  a: number | null,
  b: number | null,
  metric: MetricDef,
  side: "a" | "b"
): string {
  if (a === null || b === null || (!metric.higherBetter && !metric.lowerBetter))
    return "";
  const val = side === "a" ? a : b;
  const other = side === "a" ? b : a;
  if (val === other) return "";
  const isBetter = metric.higherBetter ? val > other : val < other;
  return isBetter ? "text-emerald-400" : "text-red-400";
}

export default function ComparePage() {
  const [code1, setCode1] = useState("");
  const [code2, setCode2] = useState("");
  const [data, setData] = useState<CompareStockItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCompare = useCallback(async () => {
    if (!code1 || !code2) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiGet<CompareResponse>(
        `/stocks/compare?codes=${code1},${code2}`
      );
      setData(res.stocks);
    } catch {
      setError("Gagal memuat data perbandingan.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [code1, code2]);

  useEffect(() => {
    if (code1 && code2) fetchCompare();
  }, [code1, code2, fetchCompare]);

  const s1 = data?.[0] ?? null;
  const s2 = data?.[1] ?? null;

  return (
    <div className="min-h-screen bg-dark-bg">
      <header className="sticky top-0 z-30 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-lg font-bold text-text-primary sm:text-xl">
                Bandingkan Saham
              </h1>
              <p className="text-xs text-text-secondary sm:text-sm">
                Perbandingan 2 Saham
              </p>
            </div>
            <nav className="flex items-center gap-3 text-sm">
              <Link href="/dashboard" className="text-text-secondary hover:text-emerald-400 transition-colors">
                Dashboard
              </Link>
              <Link href="/today" className="text-text-secondary hover:text-emerald-400 transition-colors">
                Saham Hari Ini
              </Link>
              <span className="text-emerald-400 font-medium">Bandingkan</span>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Selectors */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <StockSelector label="Saham 1" value={code1} onChange={setCode1} />
          <div className="hidden sm:flex items-end pb-2 text-text-muted font-bold">
            VS
          </div>
          <StockSelector label="Saham 2" value={code2} onChange={setCode2} />
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        )}

        {!loading && s1 && s2 && (
          <>
            {/* Desktop table */}
            <div className="hidden md:block rounded-xl border border-dark-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-dark-surface border-b border-dark-border">
                    <th className="text-left px-4 py-3 text-text-muted font-medium">
                      Metrik
                    </th>
                    <th className="text-right px-4 py-3 text-emerald-400 font-bold">
                      {s1.code}
                    </th>
                    <th className="text-right px-4 py-3 text-blue-400 font-bold">
                      {s2.code}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {METRICS.map((m, i) => {
                    const v1 = s1[m.key];
                    const v2 = s2[m.key];
                    const fmt = m.format ?? fmtVal;
                    const c1 = cellColor(
                      v1 as number | null,
                      v2 as number | null,
                      m,
                      "a"
                    );
                    const c2 = cellColor(
                      v1 as number | null,
                      v2 as number | null,
                      m,
                      "b"
                    );
                    return (
                      <tr
                        key={m.key}
                        className={`border-b border-dark-border ${i % 2 === 0 ? "bg-dark-bg" : "bg-dark-surface"}`}
                      >
                        <td className="px-4 py-3 text-text-secondary">
                          {m.label}
                        </td>
                        <td
                          className={`px-4 py-3 text-right font-medium ${c1 || "text-text-primary"}`}
                        >
                          {fmt(v1 as number | null)}
                        </td>
                        <td
                          className={`px-4 py-3 text-right font-medium ${c2 || "text-text-primary"}`}
                        >
                          {fmt(v2 as number | null)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile stacked */}
            <div className="md:hidden space-y-3">
              {METRICS.map((m) => {
                const v1 = s1[m.key];
                const v2 = s2[m.key];
                const fmt = m.format ?? fmtVal;
                const c1 = cellColor(
                  v1 as number | null,
                  v2 as number | null,
                  m,
                  "a"
                );
                const c2 = cellColor(
                  v1 as number | null,
                  v2 as number | null,
                  m,
                  "b"
                );
                return (
                  <div
                    key={m.key}
                    className="rounded-lg border border-dark-border bg-dark-surface p-3"
                  >
                    <p className="text-xs text-text-muted mb-2">{m.label}</p>
                    <div className="flex justify-between">
                      <div>
                        <p className="text-[10px] text-emerald-400">{s1.code}</p>
                        <p
                          className={`font-medium ${c1 || "text-text-primary"}`}
                        >
                          {fmt(v1 as number | null)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-blue-400">{s2.code}</p>
                        <p
                          className={`font-medium ${c2 || "text-text-primary"}`}
                        >
                          {fmt(v2 as number | null)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {!loading && !data && code1 && code2 && !error && (
          <p className="text-center text-text-muted py-10">
            Pilih 2 saham untuk membandingkan
          </p>
        )}

        {!code1 && !code2 && (
          <p className="text-center text-text-muted py-10">
            Pilih 2 saham di atas untuk memulai perbandingan
          </p>
        )}
      </main>
    </div>
  );
}
