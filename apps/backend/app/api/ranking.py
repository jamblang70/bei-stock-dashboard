"""Ranking API router."""

import math

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import asc, desc, func, select, text
from sqlalchemy.orm import Session, aliased

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
    sector: str | None = Query(None, description="Filter by sector"),
    syariah: bool | None = Query(None, description="Filter syariah stocks only"),
    sort_by: str = Query("score", description="Sort field: score, code, name, last_price, per, pbv, roe, dividend_yield"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return ranked list of stocks with score, price, and fundamental metrics."""
    _add_data_warning(response, db)

    # Get all active stocks
    stocks_query = db.query(Stock).filter(Stock.is_active == True)  # noqa: E712
    if sector:
        stocks_query = stocks_query.filter(Stock.sector == sector)
    if syariah:
        stocks_query = stocks_query.filter(Stock.is_syariah == True)  # noqa: E712

    total = stocks_query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    # Determine sort order for Python-side sorting
    reverse = sort_order.lower() != "asc"

    stocks = stocks_query.all()

    # Build result rows by fetching latest data per stock
    rows = []
    for stock in stocks:
        latest_score = (
            db.query(StockScore)
            .filter(StockScore.stock_id == stock.id)
            .order_by(StockScore.calculated_at.desc())
            .first()
        )
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .first()
        )
        latest_fund = (
            db.query(FundamentalData)
            .filter(FundamentalData.stock_id == stock.id)
            .order_by(FundamentalData.period_year.desc())
            .first()
        )

        score_val = float(latest_score.score) if latest_score and latest_score.score is not None else None
        price_val = float(latest_price.price) if latest_price and latest_price.price is not None else None
        change_pct = float(latest_price.change_pct) if latest_price and latest_price.change_pct is not None else None
        per_val = float(latest_fund.per) if latest_fund and latest_fund.per is not None else None
        pbv_val = float(latest_fund.pbv) if latest_fund and latest_fund.pbv is not None else None
        roe_val = float(latest_fund.roe) if latest_fund and latest_fund.roe is not None else None
        div_val = float(latest_fund.dividend_yield) if latest_fund and latest_fund.dividend_yield is not None else None

        rows.append({
            "code": stock.code,
            "name": stock.name,
            "sector": stock.sector,
            "last_price": price_val,
            "change_pct": change_pct,
            "score": score_val,
            "recommendation": latest_score.recommendation if latest_score else None,
            "per": per_val,
            "pbv": pbv_val,
            "roe": roe_val,
            "dividend_yield": div_val,
            "is_syariah": stock.is_syariah,
        })

    # Sort
    sort_key_map = {
        "score": "score", "code": "code", "name": "name",
        "last_price": "last_price", "per": "per", "pbv": "pbv",
        "roe": "roe", "dividend_yield": "dividend_yield",
    }
    key = sort_key_map.get(sort_by, "score")
    rows.sort(key=lambda r: (r[key] is None, r[key] if r[key] is not None else 0), reverse=reverse)

    # Paginate
    offset = (page - 1) * per_page
    page_rows = rows[offset: offset + per_page]

    items = [RankingItem(**r) for r in page_rows]

    return RankingResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )
