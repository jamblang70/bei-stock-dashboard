"""Service for calculating and storing sector median metrics."""

import logging
import statistics
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.stock import FundamentalData, SectorMetrics, Stock

logger = logging.getLogger(__name__)


def calculate_sector_metrics(db: Session) -> None:
    """
    Calculate median PER, PBV, ROE, dividend_yield per sector from the most
    recent fundamental_data entries and upsert into sector_metrics.
    """
    today = date.today()

    # Fetch all active stocks with their sector and latest fundamental data
    stocks = list(
        db.execute(
            select(Stock).where(Stock.is_active == True, Stock.sector != None)  # noqa: E711, E712
        )
        .scalars()
        .all()
    )

    if not stocks:
        logger.warning("No active stocks with sector data found.")
        return

    # Group latest fundamental data by sector
    sector_data: dict[str, dict[str, list[float]]] = {}

    for stock in stocks:
        if not stock.sector:
            continue

        # Get the most recent fundamental record for this stock
        fund = db.execute(
            select(FundamentalData)
            .where(FundamentalData.stock_id == stock.id)
            .order_by(FundamentalData.period_year.desc(), FundamentalData.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        if fund is None:
            continue

        sector = stock.sector
        if sector not in sector_data:
            sector_data[sector] = {"per": [], "pbv": [], "roe": [], "dividend_yield": [], "count": []}

        if fund.per is not None:
            sector_data[sector]["per"].append(float(fund.per))
        if fund.pbv is not None:
            sector_data[sector]["pbv"].append(float(fund.pbv))
        if fund.roe is not None:
            sector_data[sector]["roe"].append(float(fund.roe))
        if fund.dividend_yield is not None:
            sector_data[sector]["dividend_yield"].append(float(fund.dividend_yield))
        sector_data[sector]["count"].append(1)

    if not sector_data:
        logger.warning("No fundamental data available for sector metrics calculation.")
        return

    rows = []
    for sector, metrics in sector_data.items():
        stock_count = len(metrics["count"])
        rows.append(
            {
                "sector": sector,
                "median_per": statistics.median(metrics["per"]) if metrics["per"] else None,
                "median_pbv": statistics.median(metrics["pbv"]) if metrics["pbv"] else None,
                "median_roe": statistics.median(metrics["roe"]) if metrics["roe"] else None,
                "median_div_yield": (
                    statistics.median(metrics["dividend_yield"])
                    if metrics["dividend_yield"]
                    else None
                ),
                "stock_count": stock_count,
                "calculated_at": today,
            }
        )

    if not rows:
        return

    stmt = insert(SectorMetrics).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sector", "calculated_at"],
        set_={
            "median_per": stmt.excluded.median_per,
            "median_pbv": stmt.excluded.median_pbv,
            "median_roe": stmt.excluded.median_roe,
            "median_div_yield": stmt.excluded.median_div_yield,
            "stock_count": stmt.excluded.stock_count,
        },
    )

    try:
        db.execute(stmt)
        db.commit()
        logger.info("Sector metrics updated for %d sectors.", len(rows))
    except Exception as exc:
        db.rollback()
        logger.error("Failed to upsert sector metrics: %s", exc)
        raise
