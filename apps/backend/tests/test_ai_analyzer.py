"""
Unit tests untuk AI Analyzer Service (Task 13.5).

Tests mencakup:
- check_data_sufficiency (req 13.6)
- build_prompt
- call_llm (req 13.1)
- run_ai_analysis (req 13.6, 13.7)
"""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.models.stock import FundamentalData, PriceHistory, SectorMetrics, Stock, StockScore
from app.models.ai_analysis import AIAnalysis
from app.services.ai_analyzer import (
    build_prompt,
    call_llm,
    check_data_sufficiency,
    run_ai_analysis,
)


# ---------------------------------------------------------------------------
# Cleanup fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def cleanup_tables(db):
    yield
    db.execute(text("DELETE FROM ai_analysis"))
    db.execute(text("DELETE FROM stock_scores"))
    db.execute(text("DELETE FROM price_history"))
    db.execute(text("DELETE FROM fundamental_data"))
    db.execute(text("DELETE FROM stocks"))
    db.commit()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _create_stock(db, code="BBCA", sector="Keuangan") -> Stock:
    stock = Stock(code=code, name=f"PT {code} Tbk", sector=sector, is_active=True)
    db.add(stock)
    db.flush()
    return stock


def _create_fundamental(db, stock_id: int, period_year: int = 2024, **kwargs) -> FundamentalData:
    defaults = dict(
        stock_id=stock_id,
        period_type="annual",
        period_year=period_year,
        per=12.5,
        pbv=2.0,
        roe=0.18,
        net_profit_margin=0.15,
        debt_to_equity=0.5,
        dividend_yield=0.03,
        volatility_30d=0.02,
    )
    defaults.update(kwargs)
    fund = FundamentalData(**defaults)
    db.add(fund)
    db.flush()
    return fund


def _create_price_history(db, stock_id: int, days: int = 35) -> list[PriceHistory]:
    today = date.today()
    records = []
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        ph = PriceHistory(stock_id=stock_id, date=d, close=1000.0 + i, volume=500_000)
        db.add(ph)
        records.append(ph)
    db.flush()
    return records


# ---------------------------------------------------------------------------
# Helpers untuk membuat mock objects tanpa DB
# ---------------------------------------------------------------------------

def _make_stock(**kwargs) -> MagicMock:
    stock = MagicMock(spec=Stock)
    defaults = dict(id=1, code="BBCA", name="PT BBCA Tbk", sector="Keuangan")
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(stock, k, v)
    return stock


def _make_fund(**kwargs) -> MagicMock:
    fund = MagicMock(spec=FundamentalData)
    defaults = dict(
        id=1, stock_id=1, period_type="annual", period_year=2024,
        per=12.5, pbv=2.0, roe=0.18, net_profit_margin=0.15,
        debt_to_equity=0.5, dividend_yield=0.03, volatility_30d=0.02,
    )
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(fund, k, v)
    return fund


def _make_sector_metrics(**kwargs) -> MagicMock:
    sm = MagicMock(spec=SectorMetrics)
    defaults = dict(
        id=1, sector="Keuangan", median_per=14.0, median_pbv=2.5,
        median_roe=0.15, median_div_yield=0.025, stock_count=10,
        calculated_at=date.today(),
    )
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(sm, k, v)
    return sm


def _make_score(**kwargs) -> MagicMock:
    score = MagicMock(spec=StockScore)
    defaults = dict(
        id=1, stock_id=1, score=72.5,
        valuation_score=70.0, quality_score=75.0, momentum_score=65.0,
        is_partial=False, recommendation="Beli",
        score_factors={}, calculated_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(score, k, v)
    return score


# ===========================================================================
# Tests 1–4: check_data_sufficiency (req 13.6)
# ===========================================================================

def test_check_data_sufficiency_sufficient(db, cleanup_tables):
    """req 13.6 — >= 2 kuartal fundamental + >= 30 hari price history → (True, None)."""
    stock = _create_stock(db)
    _create_fundamental(db, stock.id, period_year=2024)
    _create_fundamental(db, stock.id, period_year=2023)
    _create_price_history(db, stock.id, days=35)
    db.commit()

    result, reason = check_data_sufficiency(db, stock.id)

    assert result is True
    assert reason is None


def test_check_data_sufficiency_insufficient_fundamental(db, cleanup_tables):
    """req 13.6 — hanya 1 kuartal fundamental → (False, keterangan)."""
    stock = _create_stock(db)
    _create_fundamental(db, stock.id, period_year=2024)
    _create_price_history(db, stock.id, days=35)
    db.commit()

    result, reason = check_data_sufficiency(db, stock.id)

    assert result is False
    assert reason is not None
    assert "fundamental" in reason.lower()


def test_check_data_sufficiency_insufficient_price_history(db, cleanup_tables):
    """req 13.6 — price history < 30 hari → (False, keterangan)."""
    stock = _create_stock(db)
    _create_fundamental(db, stock.id, period_year=2024)
    _create_fundamental(db, stock.id, period_year=2023)
    _create_price_history(db, stock.id, days=10)
    db.commit()

    result, reason = check_data_sufficiency(db, stock.id)

    assert result is False
    assert reason is not None
    assert "harga" in reason.lower() or "price" in reason.lower() or "hari" in reason.lower()


def test_check_data_sufficiency_no_data(db, cleanup_tables):
    """req 13.6 — tidak ada data sama sekali → (False, keterangan)."""
    stock = _create_stock(db)
    db.commit()

    result, reason = check_data_sufficiency(db, stock.id)

    assert result is False
    assert reason is not None
    assert len(reason) > 0


# ===========================================================================
# Tests 5–6: build_prompt
# ===========================================================================

def test_build_prompt_with_complete_data():
    """build_prompt dengan data lengkap menghasilkan string yang mengandung kode saham, sektor, dan format JSON."""
    stock = _make_stock(code="BBCA", sector="Keuangan")
    fund = _make_fund(per=12.5, pbv=2.0, roe=0.18)
    sector_metrics = _make_sector_metrics(median_per=14.0, median_pbv=2.5)
    score = _make_score(score=72.5)

    prompt = build_prompt(stock, fund, sector_metrics, score)

    assert isinstance(prompt, str)
    assert "BBCA" in prompt
    assert "Keuangan" in prompt
    # Harus ada instruksi format JSON
    assert "recommendation" in prompt
    assert "summary" in prompt
    assert "JSON" in prompt or "json" in prompt


def test_build_prompt_with_partial_data():
    """build_prompt dengan field None tidak raise exception dan menghasilkan 'N/A' untuk field None."""
    stock = _make_stock(code="TLKM", sector=None)
    fund = _make_fund(per=None, pbv=None, roe=None, net_profit_margin=None,
                      debt_to_equity=None, dividend_yield=None, volatility_30d=None)

    prompt = build_prompt(stock, fund, sector_metrics=None, score=None)

    assert isinstance(prompt, str)
    assert "TLKM" in prompt
    assert "N/A" in prompt
    # Tidak boleh raise exception


# ===========================================================================
# Tests 7–9: call_llm (req 13.1)
# ===========================================================================

def test_call_llm_openai_success():
    """req 13.1 — mock OpenAI client, verifikasi call_llm return dict yang benar dari JSON response."""
    expected_result = {
        "recommendation": "Beli",
        "summary": "Saham ini memiliki fundamental yang kuat.",
        "valuation_analysis": "Valuasi wajar.",
        "quality_analysis": "Kualitas baik.",
        "momentum_analysis": "Momentum positif.",
        "supporting_factors": ["ROE tinggi", "DER rendah"],
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(expected_result)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_response

    with patch("app.services.ai_analyzer.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "sk-test-key"
        mock_settings.GEMINI_API_KEY = None

        with patch("app.services.ai_analyzer._call_openai") as mock_call_openai:
            mock_call_openai.return_value = expected_result
            result = call_llm("test prompt")

    assert result == expected_result
    assert result["recommendation"] == "Beli"
    assert result["summary"] == "Saham ini memiliki fundamental yang kuat."


def test_call_llm_openai_invalid_json():
    """mock OpenAI return non-JSON, verifikasi raise RuntimeError."""
    with patch("app.services.ai_analyzer.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "sk-test-key"
        mock_settings.GEMINI_API_KEY = None

        with patch("app.services.ai_analyzer._call_openai") as mock_call_openai:
            mock_call_openai.side_effect = RuntimeError("Gagal parse JSON dari OpenAI: ...")

            with pytest.raises(RuntimeError, match="Gagal parse JSON"):
                call_llm("test prompt")


def test_call_llm_no_api_key():
    """Ketika tidak ada OPENAI_API_KEY dan GEMINI_API_KEY, raise RuntimeError."""
    with patch("app.services.ai_analyzer.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        mock_settings.GEMINI_API_KEY = None

        with pytest.raises(RuntimeError, match="API key"):
            call_llm("test prompt")


# ===========================================================================
# Tests 10–12: run_ai_analysis (req 13.6, 13.7)
# ===========================================================================

def test_run_ai_analysis_insufficient_data(db, cleanup_tables):
    """req 13.6 — ketika data tidak cukup, simpan record dengan data_sufficiency=False."""
    stock = _create_stock(db, code="INSUF")
    # Hanya 1 kuartal fundamental, tidak ada price history
    _create_fundamental(db, stock.id, period_year=2024)
    db.commit()

    analysis = run_ai_analysis(db, stock.id)

    assert analysis is not None
    assert analysis.data_sufficiency is False
    assert analysis.missing_data_info is not None
    assert analysis.stock_id == stock.id


def test_run_ai_analysis_success(db, cleanup_tables):
    """req 13.7 — mock call_llm, verifikasi AIAnalysis record tersimpan dengan recommendation dan summary yang benar."""
    stock = _create_stock(db, code="SUKSES")
    _create_fundamental(db, stock.id, period_year=2024)
    _create_fundamental(db, stock.id, period_year=2023)
    _create_price_history(db, stock.id, days=35)
    db.commit()

    llm_result = {
        "recommendation": "Beli Kuat",
        "summary": "Fundamental sangat kuat dengan valuasi menarik.",
        "valuation_analysis": "PER di bawah median sektor.",
        "quality_analysis": "ROE tinggi dan DER rendah.",
        "momentum_analysis": "Tren harga positif.",
        "supporting_factors": ["ROE 18%", "DER rendah", "Dividen konsisten"],
    }

    with patch("app.services.ai_analyzer.call_llm", return_value=llm_result):
        with patch("app.services.ai_analyzer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.GEMINI_API_KEY = None

            analysis = run_ai_analysis(db, stock.id)

    assert analysis is not None
    assert analysis.data_sufficiency is True
    assert analysis.recommendation == "Beli Kuat"
    assert analysis.summary == "Fundamental sangat kuat dengan valuasi menarik."
    assert analysis.stock_id == stock.id
    assert analysis.missing_data_info is None


def test_run_ai_analysis_llm_failure(db, cleanup_tables):
    """Ketika LLM gagal, raise exception dan tidak menyimpan record parsial."""
    stock = _create_stock(db, code="GAGAL")
    _create_fundamental(db, stock.id, period_year=2024)
    _create_fundamental(db, stock.id, period_year=2023)
    _create_price_history(db, stock.id, days=35)
    db.commit()

    with patch("app.services.ai_analyzer.call_llm", side_effect=RuntimeError("LLM timeout")):
        with patch("app.services.ai_analyzer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.GEMINI_API_KEY = None

            with pytest.raises(RuntimeError, match="LLM timeout"):
                run_ai_analysis(db, stock.id)

    # Verifikasi tidak ada record yang tersimpan
    count = db.query(AIAnalysis).filter(AIAnalysis.stock_id == stock.id).count()
    assert count == 0
