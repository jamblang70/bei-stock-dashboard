"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { AIAnalysis } from "@/types";

interface AIAnalysisTabProps {
  code: string;
}

function RecommendationBadge({ rec }: { rec: string }) {
  const styles: Record<string, string> = {
    "Beli Kuat": "bg-green-600 text-white",
    Beli: "bg-green-100 text-green-800",
    Tahan: "bg-yellow-100 text-yellow-800",
    Jual: "bg-red-100 text-red-800",
  };
  const cls = styles[rec] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${cls}`}>
      {rec}
    </span>
  );
}

function Section({ title, content }: { title: string; content: string | null | undefined }) {
  if (!content) return null;
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
        {title}
      </h3>
      <p className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-sm text-gray-700 leading-relaxed">
        {content}
      </p>
    </div>
  );
}

export default function AIAnalysisTab({ code }: AIAnalysisTabProps) {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  async function fetchAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<AIAnalysis>(`/analysis/${code}/ai`);
      setAnalysis(data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Gagal memuat analisa AI.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const res = await apiPost<{ message: string }>(`/analysis/${code}/ai/refresh`);
      setRefreshMsg(res.message);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Gagal memicu analisa ulang.";
      setRefreshMsg(msg);
    } finally {
      setRefreshing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-gray-200 bg-white p-10 shadow-sm">
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <svg
            className="h-8 w-8 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          <span className="text-sm">Memuat analisa AI...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Analisa AI
        </h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          {refreshing ? "Memproses..." : "Perbarui Analisa"}
        </button>
      </div>

      {refreshMsg && (
        <div className="mb-4 rounded-lg bg-blue-50 px-4 py-2 text-sm text-blue-700">
          {refreshMsg}
        </div>
      )}

      {error && !analysis && (
        <div className="rounded-lg bg-gray-50 px-4 py-6 text-center text-sm text-gray-500">
          <p>{error}</p>
          <button
            onClick={fetchAnalysis}
            className="mt-3 text-xs text-blue-600 underline hover:text-blue-800"
          >
            Coba lagi
          </button>
        </div>
      )}

      {analysis && !analysis.data_sufficiency && (
        <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-4">
          <p className="text-sm font-medium text-yellow-800">
            Data tidak cukup untuk menghasilkan analisa AI yang akurat.
          </p>
          {analysis.missing_data_info && (
            <p className="mt-1 text-xs text-yellow-700">{analysis.missing_data_info}</p>
          )}
        </div>
      )}

      {analysis && analysis.data_sufficiency && (
        <div className="space-y-5">
          {/* Rekomendasi + Ringkasan */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-4">
            <RecommendationBadge rec={analysis.recommendation} />
            <p className="text-sm text-gray-700 leading-relaxed">{analysis.summary}</p>
          </div>

          {/* Analisa detail */}
          <Section title="Analisa Valuasi" content={analysis.valuation_analysis} />
          <Section title="Analisa Kualitas Fundamental" content={analysis.quality_analysis} />
          <Section title="Analisa Momentum" content={analysis.momentum_analysis} />

          {/* Faktor pendukung */}
          {analysis.supporting_factors && analysis.supporting_factors.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                Faktor Pendukung
              </h3>
              <ul className="space-y-1">
                {analysis.supporting_factors.map((factor, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>
              Dihasilkan:{" "}
              {new Date(analysis.generated_at).toLocaleString("id-ID", {
                dateStyle: "medium",
                timeStyle: "short",
              })}
              {analysis.model_used && analysis.model_used !== "none"
                ? ` · ${analysis.model_used}`
                : ""}
            </span>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="mt-5 text-[10px] leading-relaxed text-gray-400">
        * Analisa ini dihasilkan oleh AI dan bersifat informatif semata. Bukan merupakan
        rekomendasi investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab investor.
      </p>
    </div>
  );
}
