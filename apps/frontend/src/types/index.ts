// ─── Stock ────────────────────────────────────────────────────────────────────

export interface Stock {
  id: number;
  code: string;
  name: string;
  sector: string | null;
  sub_sector: string | null;
  is_active: boolean;
  is_syariah?: boolean;
}

export interface StockProfile extends Stock {
  description: string | null;
  listing_date: string | null;
  last_price: number | null;
  change_nominal: number | null;
  change_pct: number | null;
  volume: number | null;
  score: ScoreInfo | null;
  is_syariah?: boolean;
}

// ─── Price History ────────────────────────────────────────────────────────────

export interface PriceHistory {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  adjusted_close: number | null;
}

// ─── Fundamentals ─────────────────────────────────────────────────────────────

export interface FundamentalsData {
  period_type: string;
  period_year: number;
  // Valuasi
  per: number | null;
  pbv: number | null;
  ev_ebitda: number | null;
  // Profitabilitas
  roe: number | null;
  roa: number | null;
  net_profit_margin: number | null;
  // Likuiditas & Solvabilitas
  current_ratio: number | null;
  debt_to_equity: number | null;
  // Dividen
  dividend_yield: number | null;
  dividend_per_share: number | null;
  // Teknikal
  beta: number | null;
  volatility_30d: number | null;
  // Raw financials
  revenue: number | null;
  net_income: number | null;
  total_assets: number | null;
  total_equity: number | null;
  total_debt: number | null;
  ebitda: number | null;
  eps: number | null;
  book_value_per_share: number | null;
  published_at: string | null;
}

// ─── Score ────────────────────────────────────────────────────────────────────

export interface ScoreInfo {
  score: number;
  valuation_score: number | null;
  quality_score: number | null;
  momentum_score: number | null;
  recommendation: "Beli Kuat" | "Beli" | "Tahan" | "Jual" | null;
  is_partial: boolean;
  score_factors: string[] | null;
  calculated_at: string;
}

// ─── Watchlist ────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  id?: number;
  code: string;
  name: string;
  sector: string | null;
  price: number | null;
  change_pct: number | null;
  score: number | null;
  recommendation: string | null;
  added_at: string;
  // Legacy nested format support
  stock?: {
    id: number;
    code: string;
    name: string;
    sector: string | null;
    sub_sector: string | null;
    is_active: boolean;
  };
  last_price?: number | null;
  change_nominal?: number | null;
}

// ─── Ranking ──────────────────────────────────────────────────────────────────

export interface RankingItem {
  code: string;
  name: string;
  sector: string | null;
  last_price: number | null;
  change_pct: number | null;
  score: number | null;
  recommendation: string | null;
  per: number | null;
  pbv: number | null;
  roe: number | null;
  dividend_yield: number | null;
  is_syariah?: boolean;
}

// ─── AI Analysis ──────────────────────────────────────────────────────────────

export interface AIAnalysis {
  id: number;
  stock_code: string;
  summary: string;
  recommendation: "Beli Kuat" | "Beli" | "Tahan" | "Jual";
  valuation_analysis: string | null;
  quality_analysis: string | null;
  momentum_analysis: string | null;
  supporting_factors: string[] | null;
  data_sufficiency: boolean;
  missing_data_info: string | null;
  model_used: string | null;
  generated_at: string;
}

// ─── Sector Comparison ────────────────────────────────────────────────────────

export interface SectorComparison {
  sector: string;
  stock_per: number | null;
  sector_median_per: number | null;
  stock_pbv: number | null;
  sector_median_pbv: number | null;
  stock_roe: number | null;
  sector_median_roe: number | null;
  stock_dividend_yield: number | null;
  sector_median_dividend_yield: number | null;
  stock_count: number;
  sufficient_data: boolean;
}

// ─── API Pagination ───────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  data: T[];
  items?: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
