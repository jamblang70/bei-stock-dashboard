"""AI Analyzer Service — menghasilkan analisa saham menggunakan LLM."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd
import ta
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis
from app.models.stock import FundamentalData, PriceHistory, SectorMetrics, Stock, StockScore

logger = logging.getLogger(__name__)

PROMPT_VERSION = "2.0"


# ---------------------------------------------------------------------------
# 1. Check Data Sufficiency
# ---------------------------------------------------------------------------

def check_data_sufficiency(db: Session, stock_id: int) -> tuple[bool, str | None]:
    missing: list[str] = []

    fund_count = db.execute(
        select(func.count()).select_from(FundamentalData).where(
            FundamentalData.stock_id == stock_id
        )
    ).scalar_one()

    if fund_count < 2:
        missing.append(f"data fundamental kurang (tersedia {fund_count} kuartal, dibutuhkan minimal 2)")

    cutoff = datetime.now(tz=timezone.utc).date() - timedelta(days=30)
    price_count = db.execute(
        select(func.count()).select_from(PriceHistory).where(
            PriceHistory.stock_id == stock_id,
            PriceHistory.date >= cutoff,
        )
    ).scalar_one()

    if price_count < 15:
        missing.append(
            f"data harga historis kurang (tersedia {price_count} hari dalam 30 hari terakhir, dibutuhkan minimal 30)"
        )

    if missing:
        return False, "; ".join(missing)
    return True, None


# ---------------------------------------------------------------------------
# 2. Compute Technical Indicators
# ---------------------------------------------------------------------------

def _compute_technical(db: Session, stock_id: int) -> dict:
    """Hitung indikator teknikal dari price_history 90 hari terakhir."""
    cutoff = datetime.now(tz=timezone.utc).date() - timedelta(days=90)
    rows = db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock_id, PriceHistory.date >= cutoff)
        .order_by(PriceHistory.date.asc())
    ).scalars().all()

    if len(rows) < 14:
        return {}

    closes = pd.Series([float(r.close) for r in rows])
    latest_close = float(rows[-1].close)

    def _safe(val) -> float | None:
        try:
            v = float(val)
            return None if math.isnan(v) else round(v, 2)
        except Exception:
            return None

    ma20 = _safe(ta.trend.sma_indicator(closes, window=20).iloc[-1])
    ma50 = _safe(ta.trend.sma_indicator(closes, window=50).iloc[-1]) if len(rows) >= 50 else None
    ema20 = _safe(ta.trend.ema_indicator(closes, window=20).iloc[-1])
    rsi = _safe(ta.momentum.rsi(closes, window=14).iloc[-1])
    macd_line = _safe(ta.trend.macd(closes).iloc[-1])
    macd_signal = _safe(ta.trend.macd_signal(closes).iloc[-1])
    macd_hist = _safe(ta.trend.macd_diff(closes).iloc[-1])
    bb_upper = _safe(ta.volatility.bollinger_hband(closes).iloc[-1])
    bb_lower = _safe(ta.volatility.bollinger_lband(closes).iloc[-1])

    # Price change
    if len(rows) >= 20:
        change_1m = round((latest_close - float(rows[-20].close)) / float(rows[-20].close) * 100, 2)
    else:
        change_1m = None

    if len(rows) >= 60:
        change_3m = round((latest_close - float(rows[-60].close)) / float(rows[-60].close) * 100, 2)
    else:
        change_3m = None

    # Signals
    ma_signal = "N/A"
    if ma20 and ma50:
        if latest_close > ma20 > ma50:
            ma_signal = "Bullish (harga di atas MA20 dan MA50)"
        elif latest_close < ma20 < ma50:
            ma_signal = "Bearish (harga di bawah MA20 dan MA50)"
        elif latest_close > ma20:
            ma_signal = "Netral-Bullish (harga di atas MA20)"
        else:
            ma_signal = "Netral-Bearish (harga di bawah MA20)"

    rsi_signal = "N/A"
    if rsi is not None:
        if rsi >= 70:
            rsi_signal = f"Overbought ({rsi})"
        elif rsi <= 30:
            rsi_signal = f"Oversold ({rsi})"
        else:
            rsi_signal = f"Netral ({rsi})"

    macd_signal_str = "N/A"
    if macd_hist is not None:
        macd_signal_str = "Bullish (histogram positif)" if macd_hist > 0 else "Bearish (histogram negatif)"

    bb_signal = "N/A"
    if bb_upper and bb_lower:
        if latest_close >= bb_upper * 0.98:
            bb_signal = "Mendekati upper band (potensi overbought)"
        elif latest_close <= bb_lower * 1.02:
            bb_signal = "Mendekati lower band (potensi oversold)"
        else:
            bb_signal = "Di dalam Bollinger Bands (normal)"

    return {
        "latest_close": latest_close,
        "ma20": ma20,
        "ma50": ma50,
        "ema20": ema20,
        "rsi": rsi,
        "macd_line": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "change_1m": change_1m,
        "change_3m": change_3m,
        "ma_signal": ma_signal,
        "rsi_signal": rsi_signal,
        "macd_signal_str": macd_signal_str,
        "bb_signal": bb_signal,
    }


# ---------------------------------------------------------------------------
# 3. Build Prompt
# ---------------------------------------------------------------------------

def build_prompt(
    stock: Stock,
    fund: FundamentalData,
    sector_metrics: SectorMetrics | None,
    score: StockScore | None,
    technical: dict | None = None,
) -> str:
    def fmt(val, decimals: int = 2, suffix: str = "") -> str:
        if val is None:
            return "N/A"
        return f"{float(val):.{decimals}f}{suffix}"

    sector_per = fmt(sector_metrics.median_per if sector_metrics else None)
    sector_pbv = fmt(sector_metrics.median_pbv if sector_metrics else None)
    score_val = fmt(score.score if score else None, 1)

    t = technical or {}
    change_1m = f"{t.get('change_1m', 'N/A')}%" if t.get('change_1m') is not None else "N/A"
    change_3m = f"{t.get('change_3m', 'N/A')}%" if t.get('change_3m') is not None else "N/A"

    prompt = f"""Kamu adalah analis saham profesional Indonesia. Analisa saham berikut berdasarkan data fundamental DAN teknikal yang diberikan.

Data Saham: {stock.code} - {stock.name}
Sektor: {stock.sector or "N/A"}

=== DATA FUNDAMENTAL ===
- PER: {fmt(fund.per)} (median sektor: {sector_per})
- PBV: {fmt(fund.pbv)} (median sektor: {sector_pbv})
- ROE: {fmt(fund.roe, 2, "%")}
- ROA: {fmt(fund.roa, 2, "%")}
- DER: {fmt(fund.debt_to_equity)}
- Net Profit Margin: {fmt(fund.net_profit_margin, 2, "%")}
- Current Ratio: {fmt(fund.current_ratio)}
- Dividend Yield: {fmt(fund.dividend_yield, 2, "%")}
- EPS: {fmt(fund.eps)}

=== DATA TEKNIKAL ===
- Harga Terakhir: {fmt(t.get('latest_close'), 0)}
- Perubahan 1 Bulan: {change_1m}
- Perubahan 3 Bulan: {change_3m}
- MA20: {fmt(t.get('ma20'), 0)} | MA50: {fmt(t.get('ma50'), 0)}
- Sinyal MA: {t.get('ma_signal', 'N/A')}
- RSI (14): {t.get('rsi_signal', 'N/A')}
- MACD: {t.get('macd_signal_str', 'N/A')}
- Bollinger Bands: {t.get('bb_signal', 'N/A')}

=== SKOR INTERNAL ===
Skor: {score_val}/100

Berikan analisa komprehensif yang menggabungkan fundamental dan teknikal dalam format JSON berikut (tanpa markdown, hanya JSON murni):
{{
  "recommendation": "Beli Kuat|Beli|Tahan|Jual",
  "summary": "ringkasan 2-3 kalimat yang mencakup kondisi fundamental dan teknikal dalam Bahasa Indonesia",
  "valuation_analysis": "analisa valuasi fundamental dalam Bahasa Indonesia",
  "quality_analysis": "analisa kualitas fundamental (profitabilitas, likuiditas) dalam Bahasa Indonesia",
  "momentum_analysis": "analisa teknikal (RSI, MACD, MA, BB) dalam Bahasa Indonesia",
  "supporting_factors": ["faktor pendukung 1", "faktor pendukung 2", "faktor pendukung 3"]
}}"""

    return prompt


# ---------------------------------------------------------------------------
# 3. Call LLM
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> dict:
    """
    Panggil OpenAI atau Gemini API berdasarkan env var yang tersedia.

    Returns:
        dict hasil parsing JSON dari LLM.

    Raises:
        RuntimeError jika tidak ada API key atau LLM gagal.
    """
    if settings.OPENAI_API_KEY:
        return _call_openai(prompt)
    elif settings.GEMINI_API_KEY:
        return _call_gemini(prompt)
    else:
        raise RuntimeError(
            "Tidak ada LLM API key yang dikonfigurasi. "
            "Set OPENAI_API_KEY atau GEMINI_API_KEY di environment."
        )


def _call_openai(prompt: str) -> dict:
    """Panggil OpenAI API menggunakan openai package."""
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah analis saham profesional Indonesia. Selalu jawab dalam format JSON yang valid.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI mengembalikan respons kosong.")
        return json.loads(content)
    except ImportError:
        raise RuntimeError("Package 'openai' tidak terinstall. Jalankan: pip install openai>=1.35.0")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gagal parse JSON dari OpenAI: {e}")
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {e}") from e


def _call_gemini(prompt: str) -> dict:
    """Panggil Gemini API menggunakan httpx."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": settings.GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Gemini API HTTP error {e.response.status_code}: {e.response.text}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Format respons Gemini tidak terduga: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gagal parse JSON dari Gemini: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e


# ---------------------------------------------------------------------------
# 4. Save Analysis
# ---------------------------------------------------------------------------

def save_analysis(
    db: Session,
    stock_id: int,
    result: dict,
    model_used: str,
    data_sufficiency: bool,
    missing_data_info: str | None,
) -> AIAnalysis:
    """Simpan hasil analisa AI ke tabel ai_analysis."""
    now = datetime.now(tz=timezone.utc)

    analysis = AIAnalysis(
        stock_id=stock_id,
        summary=result.get("summary", ""),
        recommendation=result.get("recommendation", "Tahan"),
        valuation_analysis=result.get("valuation_analysis"),
        quality_analysis=result.get("quality_analysis"),
        momentum_analysis=result.get("momentum_analysis"),
        supporting_factors=result.get("supporting_factors"),
        data_sufficiency=data_sufficiency,
        missing_data_info=missing_data_info,
        model_used=model_used,
        prompt_version=PROMPT_VERSION,
        generated_at=now,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


# ---------------------------------------------------------------------------
# 5. Run AI Analysis (orchestrator)
# ---------------------------------------------------------------------------

def run_ai_analysis(db: Session, stock_id: int) -> AIAnalysis:
    """
    Orkestrasi lengkap analisa AI untuk satu emiten.

    Langkah:
    1. Check data sufficiency
    2. Jika tidak cukup: simpan record dengan data_sufficiency=False
    3. Jika cukup: build prompt → call LLM → save
    """
    # Ambil data saham
    stock = db.execute(
        select(Stock).where(Stock.id == stock_id)
    ).scalar_one_or_none()

    if stock is None:
        raise ValueError(f"Stock dengan id={stock_id} tidak ditemukan.")

    # 1. Check sufficiency
    is_sufficient, missing_info = check_data_sufficiency(db, stock_id)

    if not is_sufficient:
        logger.warning(
            "Data tidak cukup untuk %s (id=%d): %s", stock.code, stock_id, missing_info
        )
        return save_analysis(
            db=db,
            stock_id=stock_id,
            result={
                "summary": "Data tidak cukup untuk menghasilkan analisa AI yang akurat.",
                "recommendation": "Tahan",
            },
            model_used="none",
            data_sufficiency=False,
            missing_data_info=missing_info,
        )

    # 2. Ambil data untuk prompt
    fund = db.execute(
        select(FundamentalData)
        .where(FundamentalData.stock_id == stock_id)
        .order_by(FundamentalData.period_year.desc(), FundamentalData.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    sector_metrics = None
    if stock.sector:
        sector_metrics = db.execute(
            select(SectorMetrics)
            .where(SectorMetrics.sector == stock.sector)
            .order_by(SectorMetrics.calculated_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    score = db.execute(
        select(StockScore)
        .where(StockScore.stock_id == stock_id)
        .order_by(StockScore.calculated_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    # 2b. Hitung indikator teknikal
    technical = _compute_technical(db, stock_id)

    # 3. Build prompt
    prompt = build_prompt(stock, fund, sector_metrics, score, technical)

    # 4. Call LLM
    model_used = "gpt-4o-mini" if settings.OPENAI_API_KEY else "gemini-1.5-flash"
    try:
        result = call_llm(prompt)
    except Exception as exc:
        logger.error("LLM gagal untuk %s: %s", stock.code, exc)
        raise

    # 5. Save
    logger.info("Analisa AI berhasil untuk %s menggunakan %s.", stock.code, model_used)
    return save_analysis(
        db=db,
        stock_id=stock_id,
        result=result,
        model_used=model_used,
        data_sufficiency=True,
        missing_data_info=None,
    )
