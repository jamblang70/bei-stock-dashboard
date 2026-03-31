"""Stock service — business logic for stock data retrieval."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.stock import (
    DataSourceHealth,
    FundamentalData,
    PriceHistory,
    SectorMetrics,
    Stock,
    StockPrice,
    StockScore,
)

# ---------------------------------------------------------------------------
# Range mapping
# ---------------------------------------------------------------------------

_RANGE_DAYS: dict[str, int] = {
    "1w": 7,
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "5y": 1825,
}


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def search_stocks(db: Session, query: str, limit: int = 10) -> list[dict]:
    """Full-text case-insensitive search on code and name. Returns max `limit` results."""
    q = query.strip()
    if not q:
        return []

    pattern = f"%{q}%"
    rows = (
        db.query(Stock)
        .filter(
            Stock.is_active == True,  # noqa: E712
            (
                func.lower(Stock.code).like(func.lower(pattern))
                | func.lower(Stock.name).like(func.lower(pattern))
            ),
        )
        .limit(limit)
        .all()
    )

    return [{"code": s.code, "name": s.name, "sector": s.sector} for s in rows]


def get_stock_profile(db: Session, code: str) -> dict | None:
    """Return full emiten data + latest price + latest score. None if not found."""
    stock = (
        db.query(Stock)
        .filter(Stock.code == code.upper(), Stock.is_active == True)  # noqa: E712
        .first()
    )
    if not stock:
        return None

    # Latest price
    latest_price = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.recorded_at.desc())
        .first()
    )

    # Latest score
    latest_score = (
        db.query(StockScore)
        .filter(StockScore.stock_id == stock.id)
        .order_by(StockScore.calculated_at.desc())
        .first()
    )

    profile: dict = {
        "code": stock.code,
        "name": stock.name,
        "sector": stock.sector,
        "sub_sector": stock.sub_sector,
        "description": stock.description,
        "listing_date": stock.listing_date,
        "is_active": stock.is_active,
        "is_syariah": stock.is_syariah,
    }

    if latest_price:
        profile["price"] = {
            "price": float(latest_price.price),
            "open": float(latest_price.open) if latest_price.open is not None else None,
            "high": float(latest_price.high) if latest_price.high is not None else None,
            "low": float(latest_price.low) if latest_price.low is not None else None,
            "close": float(latest_price.close) if latest_price.close is not None else None,
            "volume": latest_price.volume,
            "change_nominal": float(latest_price.change_nominal) if latest_price.change_nominal is not None else None,
            "change_pct": float(latest_price.change_pct) if latest_price.change_pct is not None else None,
            "recorded_at": latest_price.recorded_at,
        }
    else:
        profile["price"] = None

    if latest_score:
        profile["score"] = {
            "score": float(latest_score.score),
            "valuation_score": float(latest_score.valuation_score) if latest_score.valuation_score is not None else None,
            "quality_score": float(latest_score.quality_score) if latest_score.quality_score is not None else None,
            "momentum_score": float(latest_score.momentum_score) if latest_score.momentum_score is not None else None,
            "is_partial": latest_score.is_partial,
            "recommendation": latest_score.recommendation,
            "score_factors": latest_score.score_factors,
            "calculated_at": latest_score.calculated_at,
        }
    else:
        profile["score"] = None

    return profile


def get_price_history(db: Session, code: str, range_str: str) -> list[dict]:
    """Return OHLCV price history for the given range string."""
    days = _RANGE_DAYS.get(range_str, 30)
    cutoff = date.today() - timedelta(days=days)

    stock = db.query(Stock).filter(Stock.code == code.upper()).first()
    if not stock:
        return []

    rows = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.stock_id == stock.id,
            PriceHistory.date >= cutoff,
        )
        .order_by(PriceHistory.date.asc())
        .all()
    )

    return [
        {
            "date": r.date,
            "open": float(r.open) if r.open is not None else None,
            "high": float(r.high) if r.high is not None else None,
            "low": float(r.low) if r.low is not None else None,
            "close": float(r.close),
            "volume": r.volume,
        }
        for r in rows
    ]


def get_fundamentals(db: Session, code: str) -> dict | None:
    """Return the latest fundamental data for the given stock code."""
    stock = db.query(Stock).filter(Stock.code == code.upper()).first()
    if not stock:
        return None

    fd = (
        db.query(FundamentalData)
        .filter(FundamentalData.stock_id == stock.id)
        .order_by(FundamentalData.period_year.desc(), FundamentalData.period_type.desc())
        .first()
    )
    if not fd:
        return None

    return {
        "period_type": fd.period_type,
        "period_year": fd.period_year,
        "per": float(fd.per) if fd.per is not None else None,
        "pbv": float(fd.pbv) if fd.pbv is not None else None,
        "ev_ebitda": float(fd.ev_ebitda) if fd.ev_ebitda is not None else None,
        "roe": float(fd.roe) if fd.roe is not None else None,
        "roa": float(fd.roa) if fd.roa is not None else None,
        "net_profit_margin": float(fd.net_profit_margin) if fd.net_profit_margin is not None else None,
        "current_ratio": float(fd.current_ratio) if fd.current_ratio is not None else None,
        "debt_to_equity": float(fd.debt_to_equity) if fd.debt_to_equity is not None else None,
        "dividend_yield": float(fd.dividend_yield) if fd.dividend_yield is not None else None,
        "dividend_per_share": float(fd.dividend_per_share) if fd.dividend_per_share is not None else None,
        "beta": float(fd.beta) if fd.beta is not None else None,
        "volatility_30d": float(fd.volatility_30d) if fd.volatility_30d is not None else None,
        "revenue": fd.revenue,
        "net_income": fd.net_income,
        "total_assets": fd.total_assets,
        "total_equity": fd.total_equity,
        "total_debt": fd.total_debt,
        "ebitda": fd.ebitda,
        "eps": float(fd.eps) if fd.eps is not None else None,
        "book_value_per_share": float(fd.book_value_per_share) if fd.book_value_per_share is not None else None,
        "published_at": fd.published_at,
    }


def get_sector_comparison(db: Session, code: str) -> dict | None:
    """
    Compare emiten metrics vs sector median from sector_metrics.
    Returns None if sector has < 3 emitens or stock not found.
    """
    stock = db.query(Stock).filter(Stock.code == code.upper()).first()
    if not stock or not stock.sector:
        return None

    # Check sector has >= 3 active stocks
    sector_count = (
        db.query(func.count(Stock.id))
        .filter(Stock.sector == stock.sector, Stock.is_active == True)  # noqa: E712
        .scalar()
    )
    if sector_count < 3:
        return None

    # Latest sector metrics
    sector_m = (
        db.query(SectorMetrics)
        .filter(SectorMetrics.sector == stock.sector)
        .order_by(SectorMetrics.calculated_at.desc())
        .first()
    )
    if not sector_m:
        return None

    # Latest fundamentals for this stock
    fd = (
        db.query(FundamentalData)
        .filter(FundamentalData.stock_id == stock.id)
        .order_by(FundamentalData.period_year.desc(), FundamentalData.period_type.desc())
        .first()
    )

    emiten_per = float(fd.per) if fd and fd.per is not None else None
    emiten_pbv = float(fd.pbv) if fd and fd.pbv is not None else None
    emiten_roe = float(fd.roe) if fd and fd.roe is not None else None
    emiten_div = float(fd.dividend_yield) if fd and fd.dividend_yield is not None else None

    median_per = float(sector_m.median_per) if sector_m.median_per is not None else None
    median_pbv = float(sector_m.median_pbv) if sector_m.median_pbv is not None else None
    median_roe = float(sector_m.median_roe) if sector_m.median_roe is not None else None
    median_div = float(sector_m.median_div_yield) if sector_m.median_div_yield is not None else None

    def _compare_lower_better(val: float | None, median: float | None) -> str:
        """Lower is better (PER, PBV)."""
        if val is None or median is None:
            return "neutral"
        if val < median:
            return "better"
        if val > median:
            return "worse"
        return "neutral"

    def _compare_higher_better(val: float | None, median: float | None) -> str:
        """Higher is better (ROE, div_yield)."""
        if val is None or median is None:
            return "neutral"
        if val > median:
            return "better"
        if val < median:
            return "worse"
        return "neutral"

    return {
        "emiten": {
            "per": emiten_per,
            "pbv": emiten_pbv,
            "roe": emiten_roe,
            "div_yield": emiten_div,
        },
        "sektor": {
            "median_per": median_per,
            "median_pbv": median_pbv,
            "median_roe": median_roe,
            "median_div_yield": median_div,
        },
        "indicators": {
            "per": _compare_lower_better(emiten_per, median_per),
            "pbv": _compare_lower_better(emiten_pbv, median_pbv),
            "roe": _compare_higher_better(emiten_roe, median_roe),
            "div_yield": _compare_higher_better(emiten_div, median_div),
        },
    }


def get_all_sectors(db: Session) -> list[str]:
    """Return list of unique sectors from active stocks."""
    rows = (
        db.query(Stock.sector)
        .filter(Stock.is_active == True, Stock.sector.isnot(None))  # noqa: E712
        .distinct()
        .order_by(Stock.sector.asc())
        .all()
    )
    return [r.sector for r in rows]


def check_data_source_health(db: Session) -> bool:
    """Return True if all data sources are healthy."""
    unhealthy = (
        db.query(DataSourceHealth)
        .filter(DataSourceHealth.is_healthy == False)  # noqa: E712
        .first()
    )
    return unhealthy is None
