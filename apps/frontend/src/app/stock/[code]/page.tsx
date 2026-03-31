import { notFound } from "next/navigation";
import Link from "next/link";
import StockHeader from "@/components/stock/StockHeader";
import MetricsCard from "@/components/stock/MetricsCard";
import PriceChart from "@/components/stock/PriceChart";
import ScoreCard from "@/components/stock/ScoreCard";
import AnalysisTab from "@/components/stock/AnalysisTab";
import AIAnalysisTab from "@/components/stock/AIAnalysisTab";
import SectorComparison from "@/components/stock/SectorComparison";
import AddToWatchlistButton from "@/components/watchlist/AddToWatchlistButton";
import type { StockProfile, FundamentalsData, SectorComparison as SectorComparisonType } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://bei-stock-dashboard-production.up.railway.app/api/v1";

async function fetchStockProfile(code: string): Promise<StockProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function fetchFundamentals(code: string): Promise<FundamentalsData | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}/fundamentals`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function fetchSectorComparison(code: string): Promise<SectorComparisonType | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}/sector-comparison`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export default async function StockProfilePage({ params }: { params: { code: string } }) {
  const code = params.code.toUpperCase();

  const [stock, fundamentals, sectorComparison] = await Promise.all([
    fetchStockProfile(code),
    fetchFundamentals(code),
    fetchSectorComparison(code),
  ]);

  if (!stock) notFound();

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Navbar — sticky, compact on mobile */}
      <header className="sticky top-0 z-30 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-emerald-400 transition-colors"
          >
            <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">Kembali ke Dashboard</span>
            <span className="sm:hidden">Dashboard</span>
          </Link>
          <AddToWatchlistButton stockCode={code} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-4 sm:py-6 sm:px-6 space-y-4 sm:space-y-6">
        {/* Stock header */}
        <StockHeader stock={stock} />

        {/* Metrics + Score — stack on mobile, side by side on desktop */}
        <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <MetricsCard fundamentals={fundamentals} />
          </div>
          <div>
            {stock.score && <ScoreCard score={stock.score} />}
          </div>
        </div>

        {/* Price chart — full width */}
        <PriceChart code={code} />

        {/* Analysis + Sector — stack on mobile */}
        <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
          <AnalysisTab fundamentals={fundamentals} />
          <SectorComparison data={sectorComparison} />
        </div>

        {/* AI Analysis */}
        <AIAnalysisTab code={code} />
      </main>
    </div>
  );
}
