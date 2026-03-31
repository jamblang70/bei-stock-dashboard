"""Stocks API router."""

import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import FundamentalData, Stock, StockPrice, StockScore
from app.schemas.stocks import (
    CompareResponse,
    CompareStockItem,
    DividendResponse,
    DividendStockItem,
    FundamentalsResponse,
    PriceHistoryItem,
    ScoreInfo,
    SectorComparisonResponse,
    StockListItem,
    StockListResponse,
    StockProfile,
    StockSearchResult,
    TodayResponse,
    TodayStockItem,
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
# GET /today  — must be defined BEFORE /{code} to avoid route conflict
# ---------------------------------------------------------------------------


@router.get("/today", response_model=TodayResponse)
def today_stocks(response: Response, db: Session = Depends(get_db)):
    """Return top gainers, top losers, and most active stocks."""
    _add_data_warning(response, db)

    # Subquery: latest recorded_at per stock
    latest_sub = (
        db.query(
            StockPrice.stock_id,
            func.max(StockPrice.recorded_at).label("max_recorded"),
        )
        .group_by(StockPrice.stock_id)
        .subquery()
    )

    # Join to get the actual price rows
    base = (
        db.query(StockPrice, Stock)
        .join(
            latest_sub,
            (StockPrice.stock_id == latest_sub.c.stock_id)
            & (StockPrice.recorded_at == latest_sub.c.max_recorded),
        )
        .join(Stock, Stock.id == StockPrice.stock_id)
        .filter(Stock.is_active == True)  # noqa: E712
    )

    def _to_item(sp: StockPrice, s: Stock) -> TodayStockItem:
        return TodayStockItem(
            code=s.code,
            name=s.name,
            sector=s.sector,
            last_price=float(sp.price) if sp.price is not None else None,
            change_pct=float(sp.change_pct) if sp.change_pct is not None else None,
            volume=sp.volume,
        )

    gainers = (
        base.filter(StockPrice.change_pct > 0)
        .order_by(StockPrice.change_pct.desc())
        .limit(5)
        .all()
    )
    losers = (
        base.filter(StockPrice.change_pct < 0)
        .order_by(StockPrice.change_pct.asc())
        .limit(5)
        .all()
    )
    active = (
        base.filter(StockPrice.volume.isnot(None))
        .order_by(StockPrice.volume.desc())
        .limit(5)
        .all()
    )

    return TodayResponse(
        top_gainers=[_to_item(sp, s) for sp, s in gainers],
        top_losers=[_to_item(sp, s) for sp, s in losers],
        most_active=[_to_item(sp, s) for sp, s in active],
    )


# ---------------------------------------------------------------------------
# GET /compare  — must be defined BEFORE /{code} to avoid route conflict
# ---------------------------------------------------------------------------


@router.get("/compare", response_model=CompareResponse)
def compare_stocks(
    response: Response,
    codes: str = Query(..., description="Comma-separated stock codes (exactly 2)"),
    db: Session = Depends(get_db),
):
    """Compare two stocks side-by-side with full profile + fundamentals + score."""
    _add_data_warning(response, db)

    code_list = [c.strip().upper() for c in codes.split(",") if c.strip()]
    if len(code_list) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Harus tepat 2 kode saham, dipisahkan koma.",
        )

    items: list[CompareStockItem] = []
    for code in code_list:
        stock = (
            db.query(Stock)
            .filter(Stock.code == code, Stock.is_active == True)  # noqa: E712
            .first()
        )
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saham {code} tidak ditemukan",
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
        latest_score = (
            db.query(StockScore)
            .filter(StockScore.stock_id == stock.id)
            .order_by(StockScore.calculated_at.desc())
            .first()
        )

        items.append(
            CompareStockItem(
                code=stock.code,
                name=stock.name,
                sector=stock.sector,
                last_price=float(latest_price.price) if latest_price and latest_price.price is not None else None,
                change_pct=float(latest_price.change_pct) if latest_price and latest_price.change_pct is not None else None,
                per=float(latest_fund.per) if latest_fund and latest_fund.per is not None else None,
                pbv=float(latest_fund.pbv) if latest_fund and latest_fund.pbv is not None else None,
                roe=float(latest_fund.roe) if latest_fund and latest_fund.roe is not None else None,
                roa=float(latest_fund.roa) if latest_fund and latest_fund.roa is not None else None,
                net_profit_margin=float(latest_fund.net_profit_margin) if latest_fund and latest_fund.net_profit_margin is not None else None,
                debt_to_equity=float(latest_fund.debt_to_equity) if latest_fund and latest_fund.debt_to_equity is not None else None,
                current_ratio=float(latest_fund.current_ratio) if latest_fund and latest_fund.current_ratio is not None else None,
                dividend_yield=float(latest_fund.dividend_yield) if latest_fund and latest_fund.dividend_yield is not None else None,
                eps=float(latest_fund.eps) if latest_fund and latest_fund.eps is not None else None,
                beta=float(latest_fund.beta) if latest_fund and latest_fund.beta is not None else None,
                score=float(latest_score.score) if latest_score and latest_score.score is not None else None,
                recommendation=latest_score.recommendation if latest_score else None,
            )
        )

    return CompareResponse(stocks=items)


# ---------------------------------------------------------------------------
# GET /dividends  — must be defined BEFORE /{code} to avoid route conflict
# ---------------------------------------------------------------------------


@router.get("/dividends", response_model=DividendResponse)
def dividend_stocks(
    response: Response,
    syariah: bool | None = Query(None, description="Filter syariah only"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return top dividend-paying stocks sorted by dividend_yield DESC."""
    _add_data_warning(response, db)

    # Subquery: latest fundamental_data per stock (highest period_year)
    latest_fund_sub = (
        db.query(
            FundamentalData.stock_id,
            func.max(FundamentalData.period_year).label("max_year"),
        )
        .group_by(FundamentalData.stock_id)
        .subquery()
    )

    # Subquery: latest stock_prices per stock
    latest_price_sub = (
        db.query(
            StockPrice.stock_id,
            func.max(StockPrice.recorded_at).label("max_recorded"),
        )
        .group_by(StockPrice.stock_id)
        .subquery()
    )

    # Subquery: latest stock_scores per stock
    latest_score_sub = (
        db.query(
            StockScore.stock_id,
            func.max(StockScore.calculated_at).label("max_calc"),
        )
        .group_by(StockScore.stock_id)
        .subquery()
    )

    query = (
        db.query(Stock, FundamentalData, StockPrice, StockScore)
        .join(
            latest_fund_sub,
            Stock.id == latest_fund_sub.c.stock_id,
        )
        .join(
            FundamentalData,
            (FundamentalData.stock_id == Stock.id)
            & (FundamentalData.period_year == latest_fund_sub.c.max_year),
        )
        .outerjoin(
            latest_price_sub,
            Stock.id == latest_price_sub.c.stock_id,
        )
        .outerjoin(
            StockPrice,
            (StockPrice.stock_id == Stock.id)
            & (StockPrice.recorded_at == latest_price_sub.c.max_recorded),
        )
        .outerjoin(
            latest_score_sub,
            Stock.id == latest_score_sub.c.stock_id,
        )
        .outerjoin(
            StockScore,
            (StockScore.stock_id == Stock.id)
            & (StockScore.calculated_at == latest_score_sub.c.max_calc),
        )
        .filter(
            Stock.is_active == True,  # noqa: E712
            FundamentalData.dividend_yield.isnot(None),
            FundamentalData.dividend_yield > 0,
        )
    )

    if syariah is True:
        query = query.filter(Stock.is_syariah == True)  # noqa: E712

    query = query.order_by(FundamentalData.dividend_yield.desc())

    total = query.count()
    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page).all()

    items: list[DividendStockItem] = []
    for stock, fund, price, score_obj in rows:
        div_yield = float(fund.dividend_yield) if fund.dividend_yield is not None else None
        div_per_share = float(fund.dividend_per_share) if fund.dividend_per_share is not None else None
        items.append(
            DividendStockItem(
                code=stock.code,
                name=stock.name,
                sector=stock.sector,
                last_price=float(price.price) if price and price.price is not None else None,
                dividend_yield=div_yield,
                dividend_per_share=div_per_share,
                annual_dividend_estimate=div_per_share,
                per=float(fund.per) if fund.per is not None else None,
                score=float(score_obj.score) if score_obj and score_obj.score is not None else None,
                is_syariah=stock.is_syariah,
            )
        )

    return DividendResponse(data=items, total=total)


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
