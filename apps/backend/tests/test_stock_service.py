"""
Unit tests for app.services.stock_service.

Tests cover:
- search_stocks: case-insensitive, by name, no results, max 10 results
- get_stock_profile: found, not found
- get_price_history: range "1m" returns data within 30 days
- get_sector_comparison: insufficient stocks (<3), sufficient stocks (>=3)
- get_all_sectors: returns unique sectors from active stocks

Database: SQLite in-memory (via conftest.py fixtures)
"""

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.stock import FundamentalData, PriceHistory, SectorMetrics, Stock
from app.services.stock_service import (
    get_all_sectors,
    get_price_history,
    get_sector_comparison,
    get_stock_profile,
    search_stocks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stocks_setup(db: Session):
    """Insert sample Stock records (and related data) for testing."""
    stocks = [
        Stock(code="BBCA", name="Bank Central Asia Tbk", sector="Keuangan", is_active=True),
        Stock(code="BBRI", name="Bank Rakyat Indonesia Tbk", sector="Keuangan", is_active=True),
        Stock(code="BMRI", name="Bank Mandiri Tbk", sector="Keuangan", is_active=True),
        Stock(code="TLKM", name="Telkom Indonesia Tbk", sector="Teknologi", is_active=True),
        Stock(code="ASII", name="Astra International Tbk", sector="Industri", is_active=True),
        Stock(code="UNVR", name="Unilever Indonesia Tbk", sector="Konsumer", is_active=True),
        Stock(code="INDF", name="Indofood Sukses Makmur Tbk", sector="Konsumer", is_active=True),
        Stock(code="ICBP", name="Indofood CBP Sukses Makmur Tbk", sector="Konsumer", is_active=True),
        Stock(code="GGRM", name="Gudang Garam Tbk", sector="Konsumer", is_active=True),
        Stock(code="HMSP", name="HM Sampoerna Tbk", sector="Konsumer", is_active=True),
        Stock(code="KLBF", name="Kalbe Farma Tbk", sector="Kesehatan", is_active=True),
        Stock(code="SIDO", name="Industri Jamu dan Farmasi Sido Muncul Tbk", sector="Kesehatan", is_active=True),
        Stock(code="KAEF", name="Kimia Farma Tbk", sector="Kesehatan", is_active=True),
        Stock(code="PTBA", name="Bukit Asam Tbk", sector="Energi", is_active=True),
        Stock(code="ADRO", name="Adaro Energy Indonesia Tbk", sector="Energi", is_active=True),
        # Inactive stock — should not appear in search
        Stock(code="ZZZZ", name="Inactive Corp", sector="Lainnya", is_active=False),
    ]
    for s in stocks:
        db.add(s)
    db.flush()

    # Add SectorMetrics for Keuangan (3 stocks) so sector comparison works
    sm = SectorMetrics(
        sector="Keuangan",
        median_per=12.5,
        median_pbv=2.0,
        median_roe=15.0,
        median_div_yield=3.0,
        stock_count=3,
        calculated_at=date.today(),
    )
    db.add(sm)

    # Add FundamentalData for BBCA
    bbca = db.query(Stock).filter(Stock.code == "BBCA").first()
    fd = FundamentalData(
        stock_id=bbca.id,
        period_type="annual",
        period_year=2023,
        per=15.0,
        pbv=3.0,
        roe=18.0,
        dividend_yield=2.5,
    )
    db.add(fd)

    # Add PriceHistory for BBCA — some within 30 days, some older
    today = date.today()
    for i in range(1, 6):
        db.add(PriceHistory(
            stock_id=bbca.id,
            date=today - timedelta(days=i),
            close=9000.0 + i * 10,
            volume=1_000_000,
        ))
    # Older than 30 days
    db.add(PriceHistory(
        stock_id=bbca.id,
        date=today - timedelta(days=45),
        close=8500.0,
        volume=500_000,
    ))

    db.commit()
    yield db

    # Cleanup
    with db.bind.begin() as conn:
        conn.execute(FundamentalData.__table__.delete())
        conn.execute(PriceHistory.__table__.delete())
        conn.execute(SectorMetrics.__table__.delete())
        conn.execute(Stock.__table__.delete())


# ---------------------------------------------------------------------------
# search_stocks tests
# ---------------------------------------------------------------------------


def test_search_stocks_case_insensitive(stocks_setup):
    """Req 2.4 — search "bbca" (lowercase) should find stock with code "BBCA"."""
    results = search_stocks(stocks_setup, "bbca")
    codes = [r["code"] for r in results]
    assert "BBCA" in codes


def test_search_stocks_by_name(stocks_setup):
    """Req 2.4 — search "bank central" should find stock whose name contains those words."""
    results = search_stocks(stocks_setup, "bank central")
    names = [r["name"] for r in results]
    assert any("Bank Central" in n for n in names)


def test_search_stocks_no_results(stocks_setup):
    """Req 2.3 — search "ZZZZZ" should return an empty list."""
    results = search_stocks(stocks_setup, "ZZZZZ")
    assert results == []


def test_search_stocks_max_10_results(stocks_setup):
    """Req 2.5 — if more than 10 stocks match, only 10 should be returned."""
    # "Tbk" appears in all 15 active stock names
    results = search_stocks(stocks_setup, "Tbk")
    assert len(results) <= 10


# ---------------------------------------------------------------------------
# get_stock_profile tests
# ---------------------------------------------------------------------------


def test_get_stock_profile_found(stocks_setup):
    """get_stock_profile should return a dict with code, name, sector for an existing stock."""
    profile = get_stock_profile(stocks_setup, "BBCA")
    assert profile is not None
    assert profile["code"] == "BBCA"
    assert "name" in profile
    assert "sector" in profile


def test_get_stock_profile_not_found(stocks_setup):
    """get_stock_profile should return None for a non-existent stock code."""
    profile = get_stock_profile(stocks_setup, "XXXX")
    assert profile is None


# ---------------------------------------------------------------------------
# get_price_history tests
# ---------------------------------------------------------------------------


def test_get_price_history_range(stocks_setup):
    """get_price_history with range "1m" should only return data within the last 30 days."""
    history = get_price_history(stocks_setup, "BBCA", "1m")
    assert len(history) > 0

    cutoff = date.today() - timedelta(days=30)
    for entry in history:
        assert entry["date"] >= cutoff, f"Entry date {entry['date']} is older than 30 days"


# ---------------------------------------------------------------------------
# get_sector_comparison tests
# ---------------------------------------------------------------------------


def test_sector_comparison_insufficient_stocks(stocks_setup):
    """Req 8.4 — get_sector_comparison should return None if sector has < 3 active stocks."""
    # "Energi" has only 2 stocks (PTBA, ADRO) — no SectorMetrics either
    result = get_sector_comparison(stocks_setup, "PTBA")
    assert result is None


def test_sector_comparison_sufficient_stocks(stocks_setup):
    """get_sector_comparison should return dict with emiten, sektor, indicators if >= 3 stocks."""
    # "Keuangan" has 3 stocks (BBCA, BBRI, BMRI) and SectorMetrics + FundamentalData for BBCA
    result = get_sector_comparison(stocks_setup, "BBCA")
    assert result is not None
    assert "emiten" in result
    assert "sektor" in result
    assert "indicators" in result


# ---------------------------------------------------------------------------
# get_all_sectors tests
# ---------------------------------------------------------------------------


def test_get_all_sectors(stocks_setup):
    """get_all_sectors should return a list of unique sectors from active stocks only."""
    sectors = get_all_sectors(stocks_setup)
    assert isinstance(sectors, list)
    # Should not contain duplicates
    assert len(sectors) == len(set(sectors))
    # Should contain sectors from active stocks
    assert "Keuangan" in sectors
    assert "Teknologi" in sectors
    # Inactive stock's sector should not appear if it's the only stock in that sector
    # "Lainnya" only has the inactive ZZZZ stock, so it should not appear
    assert "Lainnya" not in sectors
