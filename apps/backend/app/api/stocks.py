"""Stocks API router."""

import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import Stock, StockScore
from app.schemas.stocks import (
    FundamentalsResponse,
    PriceHistoryItem,
    ScoreInfo,
    SectorComparisonResponse,
    StockListItem,
    StockListResponse,
    StockProfile,
    StockSearchResult,
)
from app.services.stock_service import (
    check_data_source_health,
    get_all_sectors,
    get_fundamentals,
    get_price_history,
    get_sector_comparison,
    get_stock_profile,
    search_stocks,
)

router = APIRouter()


def _add_data_warning(response: Response, db: Session) -> None:
    """Add X-Data-Warning header if any data source is unhealthy."""
    if not check_data_source_health(db):
        response.headers["X-Data-Warning"] = "true"


# ---------------------------------------------------------------------------
# GET /sectors  — must be defined BEFORE /{code} to avoid route conflict
# ---------------------------------------------------------------------------


@router.get("/sectors", response_model=list[str])
def list_sectors(response: Response, db: Session = Depends(get_db)):
    """Return list of all unique sectors from active stocks."""
    _add_data_warning(response, db)
    return get_all_sectors(db)


# ---------------------------------------------------------------------------
# GET /search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=list[StockSearchResult])
def search(
    response: Response,
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
):
    """Search stocks by code or name (case-insensitive, max 10 results)."""
    _add_data_warning(response, db)
    results = search_stocks(db, q, limit=10)
    return results


# ---------------------------------------------------------------------------
# GET /  — list all stocks with filter, sort, pagination
# ---------------------------------------------------------------------------


@router.get("/", response_model=StockListResponse)
def list_stocks(
    response: Response,
    sector: str | None = Query(None, description="Filter by sector"),
    sort_by: str = Query("code", description="Sort field: code, name, sector"),
    sort_order: str = Query("asc", description="asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all active stocks with optional sector filter, sorting, and pagination."""
    _add_data_warning(response, db)

    query = db.query(Stock).filter(Stock.is_active == True)  # noqa: E712

    if sector:
        query = query.filter(Stock.sector == sector)

    # Sorting
    sort_col = getattr(Stock, sort_by, Stock.code)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page
    stocks = query.offset(offset).limit(per_page).all()

    return StockListResponse(
        data=[
            StockListItem(
                code=s.code,
                name=s.name,
                sector=s.sector,
                sub_sector=s.sub_sector,
                is_active=s.is_active,
            )
            for s in stocks
        ],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /{code}
# ---------------------------------------------------------------------------


@router.get("/{code}", response_model=StockProfile)
def get_stock(code: str, response: Response, db: Session = Depends(get_db)):
    """Return full stock profile including latest price and score."""
    _add_data_warning(response, db)
    profile = get_stock_profile(db, code)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saham tidak ditemukan")
    return profile


# ---------------------------------------------------------------------------
# GET /{code}/price-history
# ---------------------------------------------------------------------------


@router.get("/{code}/price-history", response_model=list[PriceHistoryItem])
def price_history(
    code: str,
    response: Response,
    range: str = Query("1m", description="1w, 1m, 3m, 6m, 1y, 5y"),
    db: Session = Depends(get_db),
):
    """Return OHLCV price history for the given range."""
    _add_data_warning(response, db)
    valid_ranges = {"1w", "1m", "3m", "6m", "1y", "5y"}
    if range not in valid_ranges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Range tidak valid. Gunakan salah satu: {', '.join(sorted(valid_ranges))}",
        )
    history = get_price_history(db, code, range)
    return history


# ---------------------------------------------------------------------------
# GET /{code}/fundamentals
# ---------------------------------------------------------------------------


@router.get("/{code}/fundamentals", response_model=FundamentalsResponse)
def fundamentals(code: str, response: Response, db: Session = Depends(get_db)):
    """Return latest fundamental data for the stock."""
    _add_data_warning(response, db)
    data = get_fundamentals(db, code)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data fundamental tidak ditemukan",
        )
    return data


# ---------------------------------------------------------------------------
# GET /{code}/score
# ---------------------------------------------------------------------------


@router.get("/{code}/score", response_model=ScoreInfo)
def get_score(code: str, response: Response, db: Session = Depends(get_db)):
    """Return latest score and breakdown for the stock."""
    _add_data_warning(response, db)
    stock = db.query(Stock).filter(Stock.code == code.upper()).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saham tidak ditemukan")

    latest_score = (
        db.query(StockScore)
        .filter(StockScore.stock_id == stock.id)
        .order_by(StockScore.calculated_at.desc())
        .first()
    )
    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data score tidak ditemukan",
        )

    return ScoreInfo(
        score=float(latest_score.score),
        valuation_score=float(latest_score.valuation_score) if latest_score.valuation_score is not None else None,
        quality_score=float(latest_score.quality_score) if latest_score.quality_score is not None else None,
        momentum_score=float(latest_score.momentum_score) if latest_score.momentum_score is not None else None,
        is_partial=latest_score.is_partial,
        recommendation=latest_score.recommendation,
        score_factors=latest_score.score_factors,
        calculated_at=latest_score.calculated_at,
    )


# ---------------------------------------------------------------------------
# GET /{code}/sector-comparison
# ---------------------------------------------------------------------------


@router.get("/{code}/sector-comparison", response_model=SectorComparisonResponse)
def sector_comparison(code: str, response: Response, db: Session = Depends(get_db)):
    """Return sector comparison metrics for the stock."""
    _add_data_warning(response, db)
    data = get_sector_comparison(db, code)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data perbandingan sektor tidak tersedia (sektor < 3 emiten atau data tidak ditemukan)",
        )
    return data
