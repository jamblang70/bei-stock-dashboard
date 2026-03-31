"""Ranking API router — optimized with single JOIN query."""

import math

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import FundamentalData, Stock, StockPrice, StockScore
from app.schemas.ranking import RankingItem, RankingResponse
from app.services.stock_service import check_data_source_health

router = APIRouter()


def _add_data_warning(response: Response, db: Session) -> None:
    if not check_data_source_health(db):
        response.headers["X-Data-Warning"] = "true"


@router.get("/", response_model=RankingResponse)
def get_ranking(
    response: Response,
    sector: str | None = Query(None),
    syariah: bool | None = Query(None),
    sort_by: str = Query("score"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    _add_data_warning(response, db)

    # Latest score per stock (single query)
    latest_score_sub = (
        select(
            StockScore.stock_id,
            func.max(StockScore.calculated_at).label("max_calc"),
        )
        .group_by(StockScore.stock_id)
        .subquery()
    )

    # Latest price per stock (single query)
    latest_price_sub = (
        select(
            StockPrice.stock_id,
            func.max(StockPrice.recorded_at).label("max_rec"),
        )
        .group_by(StockPrice.stock_id)
        .subquery()
    )

    # Latest fundamental per stock (single query)
    latest_fund_sub = (
        select(
            FundamentalData.stock_id,
            func.max(FundamentalData.period_year).label("max_year"),
        )
        .group_by(FundamentalData.stock_id)
        .subquery()
    )

    # Main query — single round trip
    stmt = (
        select(
            Stock.id,
            Stock.code,
            Stock.name,
            Stock.sector,
            Stock.is_syariah,
            StockScore.score,
            StockScore.recommendation,
            StockPrice.price.label("last_price"),
            StockPrice.change_pct,
            FundamentalData.per,
            FundamentalData.pbv,
            FundamentalData.roe,
            FundamentalData.dividend_yield,
        )
        .outerjoin(latest_score_sub, Stock.id == latest_score_sub.c.stock_id)
        .outerjoin(
            StockScore,
            (StockScore.stock_id == Stock.id)
            & (StockScore.calculated_at == latest_score_sub.c.max_calc),
        )
        .outerjoin(latest_price_sub, Stock.id == latest_price_sub.c.stock_id)
        .outerjoin(
            StockPrice,
            (StockPrice.stock_id == Stock.id)
            & (StockPrice.recorded_at == latest_price_sub.c.max_rec),
        )
        .outerjoin(latest_fund_sub, Stock.id == latest_fund_sub.c.stock_id)
        .outerjoin(
            FundamentalData,
            (FundamentalData.stock_id == Stock.id)
            & (FundamentalData.period_year == latest_fund_sub.c.max_year),
        )
        .where(Stock.is_active == True)  # noqa: E712
    )

    if sector:
        stmt = stmt.where(Stock.sector == sector)
    if syariah:
        stmt = stmt.where(Stock.is_syariah == True)  # noqa: E712

    rows = db.execute(stmt).all()

    # Build dicts
    data = [
        {
            "code": r.code,
            "name": r.name,
            "sector": r.sector,
            "is_syariah": r.is_syariah,
            "score": float(r.score) if r.score is not None else None,
            "recommendation": r.recommendation,
            "last_price": float(r.last_price) if r.last_price is not None else None,
            "change_pct": float(r.change_pct) if r.change_pct is not None else None,
            "per": float(r.per) if r.per is not None else None,
            "pbv": float(r.pbv) if r.pbv is not None else None,
            "roe": float(r.roe) if r.roe is not None else None,
            "dividend_yield": float(r.dividend_yield) if r.dividend_yield is not None else None,
        }
        for r in rows
    ]

    # Sort in Python
    sort_key_map = {
        "score": "score", "code": "code", "name": "name",
        "last_price": "last_price", "per": "per", "pbv": "pbv",
        "roe": "roe", "dividend_yield": "dividend_yield",
    }
    key = sort_key_map.get(sort_by, "score")
    reverse = sort_order.lower() != "asc"
    data.sort(key=lambda r: (r[key] is None, r[key] if r[key] is not None else 0), reverse=reverse)

    total = len(data)
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page
    page_data = data[offset: offset + per_page]

    return RankingResponse(
        data=[RankingItem(**r) for r in page_data],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )
