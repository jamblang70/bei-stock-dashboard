"""AI Analyzer Service — menghasilkan analisa saham menggunakan LLM."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis
from app.models.stock import FundamentalData, PriceHistory, SectorMetrics, Stock, StockScore

logger = logging.getLogger(__name__)

PROMPT_VERSION = "1.0"


# ---------------------------------------------------------------------------
# 1. Check Data Sufficiency
# ---------------------------------------------------------------------------

def check_data_sufficiency(db: Session, stock_id: int) -> tuple[bool, str | None]:
    """
    Validasi kecukupan data untuk analisa AI.

    Returns:
        (True, None) jika data cukup.
        (False, "keterangan") jika data tidak cukup.
    """
    missing: list[str] = []

    # Cek ≥ 2 kuartal fundamental_data
    fund_count = db.execute(
        select(func.count()).select_from(FundamentalData).where(
            FundamentalData.stock_id == stock_id
        )
    ).scalar_one()

    if fund_count < 2:
        missing.append(f"data fundamental kurang (tersedia {fund_count} kuartal, dibutuhkan minimal 2)")

    # Cek ≥ 30 hari price_history
    cutoff = datetime.now(tz=timezone.utc).date() - timedelta(days=30)
    price_count = db.execute(
        select(func.count()).select_from(PriceHistory).where(
            PriceHistory.stock_id == stock_id,
            PriceHistory.date >= cutoff,
        )
    ).scalar_one()

    if price_count < 30:
        missing.append(
            f"data harga historis kurang (tersedia {price_count} hari dalam 30 hari terakhir, dibutuhkan minimal 30)"
        )

    if missing:
        return False, "; ".join(missing)
    return True, None


# ---------------------------------------------------------------------------
# 2. Build Prompt
# ---------------------------------------------------------------------------

def build_prompt(
    stock: Stock,
    fund: FundamentalData,
    sector_metrics: SectorMetrics | None,
    score: StockScore | None,
) -> str:
    """Buat prompt terstruktur Bahasa Indonesia untuk LLM."""

    def fmt(val, decimals: int = 2, suffix: str = "") -> str:
        if val is None:
            return "N/A"
        return f"{float(val):.{decimals}f}{suffix}"

    sector_per = fmt(sector_metrics.median_per if sector_metrics else None)
    sector_pbv = fmt(sector_metrics.median_pbv if sector_metrics else None)

    # Hitung perubahan harga 1 bulan dan 3 bulan dari score_factors jika ada
    change_1m = "N/A"
    change_3m = "N/A"
    vol_30d = fmt(fund.volatility_30d, 2, "%")

    if score and score.score_factors:
        factors = score.score_factors
        momentum = factors.get("momentum", {})
        # score_factors menyimpan skor, bukan perubahan langsung — gunakan N/A
        # Perubahan harga bisa diambil dari price_history jika diperlukan

    score_val = fmt(score.score if score else None, 1)

    prompt = f"""Kamu adalah analis saham profesional Indonesia. Analisa saham berikut berdasarkan data yang diberikan dan berikan penilaian objektif.

Data Saham: {stock.code} - {stock.name}
Sektor: {stock.sector or "N/A"}

Data Fundamental (kuartal terakhir):
- PER: {fmt(fund.per)} (median sektor: {sector_per})
- PBV: {fmt(fund.pbv)} (median sektor: {sector_pbv})
- ROE: {fmt(fund.roe, 2, "%")}
- DER: {fmt(fund.debt_to_equity)}
- Net Profit Margin: {fmt(fund.net_profit_margin, 2, "%")}
- Dividend Yield: {fmt(fund.dividend_yield, 2, "%")}

Momentum Teknikal:
- Perubahan 1 bulan: {change_1m}
- Perubahan 3 bulan: {change_3m}
- Volatilitas 30 hari: {vol_30d}

Skor Internal: {score_val}/100

Berikan analisa dalam format JSON berikut (tanpa markdown, hanya JSON murni):
{{
  "recommendation": "Beli Kuat|Beli|Tahan|Jual",
  "summary": "ringkasan 2-3 kalimat dalam Bahasa Indonesia",
  "valuation_analysis": "analisa valuasi dalam Bahasa Indonesia",
  "quality_analysis": "analisa kualitas fundamental dalam Bahasa Indonesia",
  "momentum_analysis": "analisa momentum teknikal dalam Bahasa Indonesia",
  "supporting_factors": ["faktor 1", "faktor 2", "faktor 3"]
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

    # 3. Build prompt
    prompt = build_prompt(stock, fund, sector_metrics, score)

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
