from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    sub_sector: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    listing_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_syariah: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    stock_prices: Mapped[List["StockPrice"]] = relationship(back_populates="stock")
    price_history: Mapped[List["PriceHistory"]] = relationship(back_populates="stock")
    fundamental_data: Mapped[List["FundamentalData"]] = relationship(back_populates="stock")
    stock_scores: Mapped[List["StockScore"]] = relationship(back_populates="stock")
    watchlists: Mapped[List["Watchlist"]] = relationship(  # noqa: F821
        back_populates="stock"
    )
    ai_analyses: Mapped[List["AIAnalysis"]] = relationship(  # noqa: F821
        back_populates="stock"
    )
    corporate_actions: Mapped[List["CorporateAction"]] = relationship(back_populates="stock")


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id"), nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    open: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    high: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    low: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    close: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    change_nominal: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    change_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stock: Mapped["Stock"] = relationship(back_populates="stock_prices")


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("stock_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    high: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    low: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    close: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    adjusted_close: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    stock: Mapped["Stock"] = relationship(back_populates="price_history")


class FundamentalData(Base):
    __tablename__ = "fundamental_data"
    __table_args__ = (UniqueConstraint("stock_id", "period_type", "period_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id"), nullable=False
    )
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    per: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    pbv: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    roe: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    roa: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    net_profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    current_ratio: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    dividend_yield: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    dividend_per_share: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    beta: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    volatility_30d: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    revenue: Mapped[Optional[int]] = mapped_column(BigInteger)
    net_income: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_assets: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_equity: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_debt: Mapped[Optional[int]] = mapped_column(BigInteger)
    ebitda: Mapped[Optional[int]] = mapped_column(BigInteger)
    eps: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    book_value_per_share: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stock: Mapped["Stock"] = relationship(back_populates="fundamental_data")


class StockScore(Base):
    __tablename__ = "stock_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    valuation_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    momentum_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False)
    recommendation: Mapped[Optional[str]] = mapped_column(String(20))
    score_factors: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stock: Mapped["Stock"] = relationship(back_populates="stock_scores")


class SectorMetrics(Base):
    __tablename__ = "sector_metrics"
    __table_args__ = (UniqueConstraint("sector", "calculated_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    median_per: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    median_pbv: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    median_roe: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    median_div_yield: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    stock_count: Mapped[Optional[int]] = mapped_column(Integer)
    calculated_at: Mapped[date] = mapped_column(Date, nullable=False)


class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    announced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stock: Mapped["Stock"] = relationship(back_populates="corporate_actions")


class DataSourceHealth(Base):
    __tablename__ = "data_source_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_failure: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
