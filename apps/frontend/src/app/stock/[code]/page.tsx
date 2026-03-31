import { notFound } from "next/navigation";
import Link from "next/link";
import StockHeader from "@/components/stock/StockHeader";
import MetricsCard from "@/components/stock/MetricsCard";
import PriceChart from "@/components/stock/PriceChart";
import ScoreCard from "@/components/stock/ScoreCard";
import AnalysisTab from "@/components/stock/AnalysisTab";
import SectorComparison from "@/components/stock/SectorComparison";
import AddToWatchlistButton from "@/components/watchlist/AddToWatchlistButton";
import type { StockProfile, FundamentalsData, SectorComparison as SectorComparisonType } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://bei-stock-dashboard-production.up.railway.app/api/v1";

async function fetchStockProfile(code: string): Promise<StockProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function fetchFundamentals(code: string): Promise<FundamentalsData | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}/fundamentals`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function fetchSectorComparison(code: string): Promise<SectorComparisonType | null> {
  try {
    const res = await fetch(`${API_BASE}/stocks/${code}/sector-comparison`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

interface PageProps {
  params: { code: string };
}

export default async function StockProfilePage({ params }: PageProps) {
  const code = params.code.toUpperCase();

  const [stock, fundamentals, sectorComparison] = await Promise.all([
    fetchStockProfile(code),
    fetchFundamentals(code),
    fetchSectorComparison(code),
  ]);

  if (!stock) notFound();

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Navbar */}
      <header className="border-b border-dark-border bg-dark-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-emerald-400 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Kembali ke Dashboard
          </Link>
          <AddToWatchlistButton stockCode={code} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <StockHeader stock={stock} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <MetricsCard fundamentals={fundamentals} />
        </div>
        <div>
          {stock.score && <ScoreCard score={stock.score} />}
        </div>
      </div>

      <PriceChart code={code} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AnalysisTab fundamentals={fundamentals} />
        <SectorComparison data={sectorComparison} />
      </div>
      </main>
    </div>
  );
}
