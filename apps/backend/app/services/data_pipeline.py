"""Data pipeline service for fetching and storing BEI stock data."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
import yfinance as yf
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.stock import (
    CorporateAction,
    DataSourceHealth,
    FundamentalData,
    PriceHistory,
    Stock,
    StockPrice,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Health monitoring
# ---------------------------------------------------------------------------

HEALTH_THRESHOLD_MINUTES = 30


def update_source_health(
    db: Session,
    source_name: str,
    is_healthy: bool,
    error_message: str | None = None,
) -> None:
    """Upsert health status for a data source into data_source_health."""
    now = datetime.now(timezone.utc)

    existing = db.execute(
        select(DataSourceHealth).where(DataSourceHealth.source_name == source_name)
    ).scalar_one_or_none()

    if existing is None:
        record = DataSourceHealth(
            source_name=source_name,
            is_healthy=is_healthy,
            last_success=now if is_healthy else None,
            last_failure=None if is_healthy else now,
            error_message=error_message,
            checked_at=now,
        )
        db.add(record)
    else:
        # Check stale BEFORE updating last_success
        was_stale = False
        if existing.last_success is not None:
            last_success = existing.last_success
            # SQLite stores naive datetimes — make timezone-aware for comparison
            if last_success.tzinfo is None:
                last_success = last_success.replace(tzinfo=timezone.utc)
            age = now - last_success
            if age > timedelta(minutes=HEALTH_THRESHOLD_MINUTES):
                was_stale = True

        existing.checked_at = now
        existing.error_message = error_message
        if is_healthy:
            existing.last_success = now
        else:
            existing.last_failure = now

        # If source was stale, mark unhealthy regardless of is_healthy param
        existing.is_healthy = False if was_stale else is_healthy

    db.commit()


def _check_source_stale(db: Session, source_name: str) -> bool:
    """Return True if the source has not succeeded within the threshold window."""
    record = db.execute(
        select(DataSourceHealth).where(DataSourceHealth.source_name == source_name)
    ).scalar_one_or_none()
    if record is None or record.last_success is None:
        return True
    now = datetime.now(timezone.utc)
    return (now - record.last_success) > timedelta(minutes=HEALTH_THRESHOLD_MINUTES)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_active_stocks(db: Session) -> list[Stock]:
    return list(db.execute(select(Stock).where(Stock.is_active == True)).scalars().all())  # noqa: E712


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        return None if (f != f) else f  # NaN check
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Task 5.1 — Fetch functions
# ---------------------------------------------------------------------------

def fetch_intraday_prices(db: Session) -> None:
    """Fetch latest prices from Yahoo Finance and upsert into stock_prices."""
    stocks = _get_active_stocks(db)
    if not stocks:
        logger.warning("No active stocks found for intraday price fetch.")
        return

    tickers = [f"{s.code}.JK" for s in stocks]
    stock_map = {f"{s.code}.JK": s for s in stocks}

    errors: list[str] = []
    now = datetime.now(timezone.utc)

    for ticker_symbol in tickers:
        stock = stock_map[ticker_symbol]
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.fast_info

            price = _safe_float(getattr(info, "last_price", None))
            if price is None:
                logger.warning("No price data for %s, skipping.", ticker_symbol)
                continue

            open_price = _safe_float(getattr(info, "open", None))
            high = _safe_float(getattr(info, "day_high", None))
            low = _safe_float(getattr(info, "day_low", None))
            volume = _safe_int(getattr(info, "three_month_average_volume", None))
            prev_close = _safe_float(getattr(info, "previous_close", None))

            change_nominal: float | None = None
            change_pct: float | None = None
            if price is not None and prev_close is not None and prev_close != 0:
                change_nominal = price - prev_close
                change_pct = (change_nominal / prev_close) * 100

            record = StockPrice(
                stock_id=stock.id,
                price=price,
                open=open_price,
                high=high,
                low=low,
                close=price,
                volume=volume,
                change_nominal=change_nominal,
                change_pct=change_pct,
                recorded_at=now,
            )
            db.add(record)

        except Exception as exc:
            err = f"{ticker_symbol}: {exc}"
            logger.error("Error fetching intraday price for %s: %s", ticker_symbol, exc)
            errors.append(err)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("DB commit failed for intraday prices: %s", exc)
        errors.append(str(exc))

    is_healthy = len(errors) == 0
    error_msg = "; ".join(errors[:5]) if errors else None
    update_source_health(db, "yahoo_finance_intraday", is_healthy, error_msg)


def fetch_daily_ohlcv(db: Session) -> None:
    """Fetch daily OHLCV data from Yahoo Finance and upsert into price_history."""
    stocks = _get_active_stocks(db)
    if not stocks:
        return

    errors: list[str] = []

    for stock in stocks:
        ticker_symbol = f"{stock.code}.JK"
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Fetch last 7 days to catch any missed days
            hist = ticker.history(period="7d", auto_adjust=True)

            if hist.empty:
                logger.warning("No OHLCV data for %s", ticker_symbol)
                continue

            rows: list[dict[str, Any]] = []
            for idx, row in hist.iterrows():
                trade_date = idx.date() if hasattr(idx, "date") else idx
                rows.append(
                    {
                        "stock_id": stock.id,
                        "date": trade_date,
                        "open": _safe_float(row.get("Open")),
                        "high": _safe_float(row.get("High")),
                        "low": _safe_float(row.get("Low")),
                        "close": _safe_float(row.get("Close")),
                        "volume": _safe_int(row.get("Volume")),
                        "adjusted_close": _safe_float(row.get("Close")),
                    }
                )

            if not rows:
                continue

            stmt = insert(PriceHistory).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["stock_id", "date"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                    "adjusted_close": stmt.excluded.adjusted_close,
                },
            )
            db.execute(stmt)
            db.commit()

        except Exception as exc:
            db.rollback()
            err = f"{ticker_symbol}: {exc}"
            logger.error("Error fetching OHLCV for %s: %s", ticker_symbol, exc)
            errors.append(err)

    is_healthy = len(errors) == 0
    error_msg = "; ".join(errors[:5]) if errors else None
    update_source_health(db, "yahoo_finance_ohlcv", is_healthy, error_msg)


def fetch_fundamental_data(db: Session) -> None:
    """Fetch fundamental data from yfinance (free) with EODHD as optional fallback."""
    stocks = _get_active_stocks(db)
    if not stocks:
        return

    errors: list[str] = []
    current_year = datetime.now().year

    for stock in stocks:
        ticker_symbol = f"{stock.code}.JK"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info or {}

            if not info or info.get("trailingPE") is None and info.get("bookValue") is None:
                logger.warning("No fundamental data for %s, skipping.", ticker_symbol)
                continue

            # Calculate derived metrics
            per = _safe_float(info.get("trailingPE") or info.get("forwardPE"))
            pbv = _safe_float(info.get("priceToBook"))
            roe = _safe_float(info.get("returnOnEquity"))
            roa = _safe_float(info.get("returnOnAssets"))
            npm = _safe_float(info.get("profitMargins"))
            current_ratio = _safe_float(info.get("currentRatio"))
            debt_to_equity = _safe_float(info.get("debtToEquity"))
            if debt_to_equity is not None:
                debt_to_equity = debt_to_equity / 100  # yfinance returns as percentage
            div_yield = _safe_float(info.get("dividendYield"))
            div_per_share = _safe_float(info.get("dividendRate"))
            beta = _safe_float(info.get("beta"))
            eps = _safe_float(info.get("trailingEps") or info.get("forwardEps"))
            book_value = _safe_float(info.get("bookValue"))
            revenue = _safe_int(info.get("totalRevenue"))
            net_income = _safe_int(info.get("netIncomeToCommon"))
            total_assets = _safe_int(info.get("totalAssets"))
            total_equity = _safe_int(info.get("totalStockholderEquity"))
            total_debt = _safe_int(info.get("totalDebt"))
            ebitda = _safe_int(info.get("ebitda"))

            # EV/EBITDA
            ev_ebitda = None
            enterprise_value = _safe_float(info.get("enterpriseValue"))
            if enterprise_value and ebitda and ebitda != 0:
                ev_ebitda = enterprise_value / ebitda

            row = {
                "stock_id": stock.id,
                "period_type": "Annual",
                "period_year": current_year,
                "per": per,
                "pbv": pbv,
                "ev_ebitda": ev_ebitda,
                "roe": roe,
                "roa": roa,
                "net_profit_margin": npm,
                "current_ratio": current_ratio,
                "debt_to_equity": debt_to_equity,
                "dividend_yield": div_yield,
                "dividend_per_share": div_per_share,
                "beta": beta,
                "volatility_30d": None,
                "revenue": revenue,
                "net_income": net_income,
                "total_assets": total_assets,
                "total_equity": total_equity,
                "total_debt": total_debt,
                "ebitda": ebitda,
                "eps": eps,
                "book_value_per_share": book_value,
                "published_at": datetime.now(timezone.utc),
            }

            stmt = insert(FundamentalData).values([row])
            stmt = stmt.on_conflict_do_update(
                index_elements=["stock_id", "period_type", "period_year"],
                set_={k: stmt.excluded[k] for k in row if k not in ("stock_id", "period_type", "period_year")},
            )
            db.execute(stmt)
            db.commit()
            logger.info("Fundamental data saved for %s", ticker_symbol)

        except Exception as exc:
            db.rollback()
            err = f"{ticker_symbol}: {exc}"
            logger.error("Error fetching fundamentals for %s: %s", ticker_symbol, exc)
            errors.append(err)

    is_healthy = len(errors) < len(stocks) // 2  # healthy if less than half failed
    error_msg = "; ".join(errors[:5]) if errors else None
    update_source_health(db, "yfinance_fundamentals", is_healthy, error_msg)


def fetch_corporate_actions(db: Session) -> None:
    """Fetch dividends and splits from Yahoo Finance and store in corporate_actions."""
    stocks = _get_active_stocks(db)
    if not stocks:
        return

    errors: list[str] = []

    for stock in stocks:
        ticker_symbol = f"{stock.code}.JK"
        try:
            ticker = yf.Ticker(ticker_symbol)

            # Dividends
            dividends = ticker.dividends
            if dividends is not None and not dividends.empty:
                for idx, amount in dividends.items():
                    action_date: date = idx.date() if hasattr(idx, "date") else idx
                    # Avoid duplicates: check existing
                    existing = db.execute(
                        select(CorporateAction).where(
                            CorporateAction.stock_id == stock.id,
                            CorporateAction.action_type == "dividend",
                            CorporateAction.action_date == action_date,
                        )
                    ).scalar_one_or_none()
                    if existing is None:
                        db.add(
                            CorporateAction(
                                stock_id=stock.id,
                                action_type="dividend",
                                action_date=action_date,
                                details={"amount": _safe_float(amount)},
                                announced_at=datetime.now(timezone.utc),
                            )
                        )

            # Splits
            splits = ticker.splits
            if splits is not None and not splits.empty:
                for idx, ratio in splits.items():
                    action_date = idx.date() if hasattr(idx, "date") else idx
                    existing = db.execute(
                        select(CorporateAction).where(
                            CorporateAction.stock_id == stock.id,
                            CorporateAction.action_type == "split",
                            CorporateAction.action_date == action_date,
                        )
                    ).scalar_one_or_none()
                    if existing is None:
                        db.add(
                            CorporateAction(
                                stock_id=stock.id,
                                action_type="split",
                                action_date=action_date,
                                details={"ratio": _safe_float(ratio)},
                                announced_at=datetime.now(timezone.utc),
                            )
                        )

            db.commit()

        except Exception as exc:
            db.rollback()
            err = f"{ticker_symbol}: {exc}"
            logger.error("Error fetching corporate actions for %s: %s", ticker_symbol, exc)
            errors.append(err)

    is_healthy = len(errors) == 0
    error_msg = "; ".join(errors[:5]) if errors else None
    update_source_health(db, "yahoo_finance_corporate_actions", is_healthy, error_msg)
