"""Pydantic schemas for stocks endpoints."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class StockSearchResult(BaseModel):
    code: str
    name: str
    sector: str | None = None


class StockListItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    sub_sector: str | None = None
    is_active: bool


class PriceInfo(BaseModel):
    price: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    change_nominal: float | None = None
    change_pct: float | None = None
    recorded_at: datetime | None = None


class ScoreInfo(BaseModel):
    score: float
    valuation_score: float | None = None
    quality_score: float | None = None
    momentum_score: float | None = None
    is_partial: bool = False
    recommendation: str | None = None
    score_factors: dict[str, Any] | None = None
    calculated_at: datetime | None = None


class StockProfile(BaseModel):
    code: str
    name: str
    sector: str | None = None
    sub_sector: str | None = None
    description: str | None = None
    listing_date: date | None = None
    is_active: bool
    price: PriceInfo | None = None
    score: ScoreInfo | None = None


class PriceHistoryItem(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: int | None = None


class FundamentalsResponse(BaseModel):
    period_type: str
    period_year: int
    per: float | None = None
    pbv: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    roa: float | None = None
    net_profit_margin: float | None = None
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    dividend_yield: float | None = None
    dividend_per_share: float | None = None
    beta: float | None = None
    volatility_30d: float | None = None
    revenue: int | None = None
    net_income: int | None = None
    total_assets: int | None = None
    total_equity: int | None = None
    total_debt: int | None = None
    ebitda: int | None = None
    eps: float | None = None
    book_value_per_share: float | None = None
    published_at: datetime | None = None


class SectorComparisonEmiten(BaseModel):
    per: float | None = None
    pbv: float | None = None
    roe: float | None = None
    div_yield: float | None = None


class SectorComparisonSektor(BaseModel):
    median_per: float | None = None
    median_pbv: float | None = None
    median_roe: float | None = None
    median_div_yield: float | None = None


class SectorComparisonIndicators(BaseModel):
    per: str
    pbv: str
    roe: str
    div_yield: str


class SectorComparisonResponse(BaseModel):
    emiten: SectorComparisonEmiten
    sektor: SectorComparisonSektor
    indicators: SectorComparisonIndicators


class StockListResponse(BaseModel):
    data: list[StockListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


# ---------------------------------------------------------------------------
# Today's Stocks
# ---------------------------------------------------------------------------


class TodayStockItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    last_price: float | None = None
    change_pct: float | None = None
    volume: int | None = None


class TodayResponse(BaseModel):
    top_gainers: list[TodayStockItem]
    top_losers: list[TodayStockItem]
    most_active: list[TodayStockItem]


# ---------------------------------------------------------------------------
# Stock Comparison
# ---------------------------------------------------------------------------


class CompareStockItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    last_price: float | None = None
    change_pct: float | None = None
    per: float | None = None
    pbv: float | None = None
    roe: float | None = None
    roa: float | None = None
    net_profit_margin: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    dividend_yield: float | None = None
    eps: float | None = None
    beta: float | None = None
    score: float | None = None
    recommendation: str | None = None


class CompareResponse(BaseModel):
    stocks: list[CompareStockItem]


# ---------------------------------------------------------------------------
# Dividend Tracker
# ---------------------------------------------------------------------------


class DividendStockItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    last_price: float | None = None
    dividend_yield: float | None = None
    dividend_per_share: float | None = None
    annual_dividend_estimate: float | None = None
    per: float | None = None
    score: float | None = None
    is_syariah: bool = False


class DividendResponse(BaseModel):
    data: list[DividendStockItem]
    total: int


# ---------------------------------------------------------------------------
# Technical Analysis
# ---------------------------------------------------------------------------


class TechnicalDataItem(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: int | None = None
    ma20: float | None = None
    ma50: float | None = None
    ma200: float | None = None
    ema20: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
