"""Scoring Engine — menghitung skor fundamental + momentum saham BEI."""

from __future__ import annotations

import logging
import statistics
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import FundamentalData, PriceHistory, SectorMetrics, Stock

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _linear_score(value: float, best: float, worst: float) -> float:
    """Map value linearly to 0–100 where best→100 and worst→0."""
    if best == worst:
        return 100.0 if value >= best else 0.0
    raw = (value - worst) / (best - worst) * 100.0
    return _clamp(raw)


# ---------------------------------------------------------------------------
# 1. Valuation Score (bobot 40%)
# ---------------------------------------------------------------------------

def calculate_valuation_score(
    fund: FundamentalData,
    sector_metrics: SectorMetrics | None,
) -> float | None:
    """
    Hitung valuation score 0–100.

    Komponen:
    - PER vs median sektor  (max 33 poin)
    - PBV vs median sektor  (max 33 poin)
    - EV/EBITDA vs historis (max 34 poin)

    Skor lebih tinggi = valuasi lebih murah (PER/PBV/EV rendah).
    Return None jika tidak ada satu pun data valuasi.
    """
    components: list[tuple[float, float]] = []  # (raw_score_0_100, weight)

    # --- PER vs median sektor ---
    per = float(fund.per) if fund.per is not None else None
    median_per = float(sector_metrics.median_per) if (sector_metrics and sector_metrics.median_per is not None) else None

    if per is not None and median_per is not None and median_per > 0:
        # PER di bawah median → lebih murah → skor tinggi
        # Rentang: 0 (2× median) → 100 (0)
        per_score = _linear_score(per, best=0.0, worst=median_per * 2)
        components.append((per_score, 33.0))
    elif per is not None and per > 0:
        # Tidak ada median sektor — gunakan absolute benchmark (PER 5–30)
        per_score = _linear_score(per, best=5.0, worst=30.0)
        components.append((per_score, 33.0))

    # --- PBV vs median sektor ---
    pbv = float(fund.pbv) if fund.pbv is not None else None
    median_pbv = float(sector_metrics.median_pbv) if (sector_metrics and sector_metrics.median_pbv is not None) else None

    if pbv is not None and median_pbv is not None and median_pbv > 0:
        pbv_score = _linear_score(pbv, best=0.0, worst=median_pbv * 2)
        components.append((pbv_score, 33.0))
    elif pbv is not None and pbv > 0:
        pbv_score = _linear_score(pbv, best=0.5, worst=5.0)
        components.append((pbv_score, 33.0))

    # --- EV/EBITDA vs historis (absolute benchmark) ---
    ev_ebitda = float(fund.ev_ebitda) if fund.ev_ebitda is not None else None
    if ev_ebitda is not None:
        # EV/EBITDA < 5 = sangat murah, > 20 = mahal
        ev_score = _linear_score(ev_ebitda, best=5.0, worst=20.0)
        components.append((ev_score, 34.0))

    if not components:
        return None

    total_weight = sum(w for _, w in components)
    weighted_sum = sum(s * w for s, w in components)
    return _clamp(weighted_sum / total_weight)


# ---------------------------------------------------------------------------
# 2. Quality Score (bobot 40%)
# ---------------------------------------------------------------------------

def calculate_quality_score(fund: FundamentalData) -> float | None:
    """
    Hitung quality score 0–100.

    Komponen:
    - ROE              (max 30 poin): ROE > 20% = 100, ROE < 0% = 0
    - Net Profit Margin(max 25 poin): NPM > 20% = 100, NPM < 0% = 0
    - Debt-to-Equity   (max 25 poin): DER < 0.5 = 100, DER > 3 = 0
    - Current Ratio    (max 20 poin): CR > 2 = 100, CR < 1 = 0

    Return None jika tidak ada satu pun data kualitas.
    """
    components: list[tuple[float, float]] = []

    # ROE (dalam desimal, misal 0.15 = 15%)
    if fund.roe is not None:
        roe = float(fund.roe)
        roe_score = _linear_score(roe, best=0.20, worst=0.0)
        components.append((roe_score, 30.0))

    # Net Profit Margin
    if fund.net_profit_margin is not None:
        npm = float(fund.net_profit_margin)
        npm_score = _linear_score(npm, best=0.20, worst=0.0)
        components.append((npm_score, 25.0))

    # Debt-to-Equity
    if fund.debt_to_equity is not None:
        der = float(fund.debt_to_equity)
        der_score = _linear_score(der, best=0.5, worst=3.0)
        components.append((der_score, 25.0))

    # Current Ratio
    if fund.current_ratio is not None:
        cr = float(fund.current_ratio)
        cr_score = _linear_score(cr, best=2.0, worst=1.0)
        components.append((cr_score, 20.0))

    if not components:
        return None

    total_weight = sum(w for _, w in components)
    weighted_sum = sum(s * w for s, w in components)
    return _clamp(weighted_sum / total_weight)


# ---------------------------------------------------------------------------
# 3. Momentum Score (bobot 20%)
# ---------------------------------------------------------------------------

def calculate_momentum_score(stock_id: int, db: Session) -> float | None:
    """
    Hitung momentum score 0–100.

    Komponen:
    - Perubahan harga 1 bulan vs sektor (max 40 poin)
    - Perubahan harga 3 bulan vs sektor (max 40 poin)
    - Volume relatif vs MA20            (max 20 poin)

    Return None jika tidak ada data harga historis.
    """
    now = datetime.now(tz=timezone.utc).date()
    date_1m = now - timedelta(days=30)
    date_3m = now - timedelta(days=90)
    date_20d = now - timedelta(days=28)  # ~20 hari bursa

    # Ambil harga historis saham ini
    rows = list(
        db.execute(
            select(PriceHistory)
            .where(PriceHistory.stock_id == stock_id)
            .where(PriceHistory.date >= date_3m)
            .order_by(PriceHistory.date.asc())
        )
        .scalars()
        .all()
    )

    if not rows:
        return None

    latest = rows[-1]
    latest_close = float(latest.close)

    # Cari harga ~1 bulan lalu
    rows_1m = [r for r in rows if r.date <= date_1m]
    # Cari harga ~3 bulan lalu
    rows_3m_start = [r for r in rows if r.date <= date_3m]

    components: list[tuple[float, float]] = []

    # --- Perubahan 1 bulan ---
    if rows_1m:
        close_1m = float(rows_1m[-1].close)
        if close_1m > 0:
            change_1m = (latest_close - close_1m) / close_1m  # desimal
            # +20% → 100, -20% → 0
            score_1m = _linear_score(change_1m, best=0.20, worst=-0.20)
            components.append((score_1m, 40.0))

    # --- Perubahan 3 bulan ---
    if rows_3m_start:
        close_3m = float(rows_3m_start[-1].close)
        if close_3m > 0:
            change_3m = (latest_close - close_3m) / close_3m
            # +40% → 100, -40% → 0
            score_3m = _linear_score(change_3m, best=0.40, worst=-0.40)
            components.append((score_3m, 40.0))

    # --- Volume relatif vs MA20 ---
    rows_20d = [r for r in rows if r.date >= date_20d]
    volumes = [float(r.volume) for r in rows_20d if r.volume is not None]
    if len(volumes) >= 5 and latest.volume is not None:
        ma20 = statistics.mean(volumes)
        if ma20 > 0:
            rel_vol = float(latest.volume) / ma20
            # rel_vol > 2 → 100, rel_vol < 0.5 → 0
            vol_score = _linear_score(rel_vol, best=2.0, worst=0.5)
            components.append((vol_score, 20.0))

    if not components:
        return None

    total_weight = sum(w for _, w in components)
    weighted_sum = sum(s * w for s, w in components)
    return _clamp(weighted_sum / total_weight)


# ---------------------------------------------------------------------------
# 4. Determine Recommendation
# ---------------------------------------------------------------------------

def determine_recommendation(score: float) -> str:
    """
    Mapping score ke label rekomendasi.

    >= 75 → "Beli Kuat"
    60–74 → "Beli"
    40–59 → "Tahan"
    < 40  → "Jual"
    """
    if score >= 75:
        return "Beli Kuat"
    elif score >= 60:
        return "Beli"
    elif score >= 40:
        return "Tahan"
    else:
        return "Jual"


# ---------------------------------------------------------------------------
# 5. Calculate Score (main entry point)
# ---------------------------------------------------------------------------

def calculate_score(stock_id: int, db: Session) -> dict:
    """
    Hitung skor lengkap untuk satu emiten.

    Return dict:
    {
        score, valuation_score, quality_score, momentum_score,
        is_partial, recommendation, score_factors
    }
    """
    # Ambil fundamental terbaru
    fund: FundamentalData | None = db.execute(
        select(FundamentalData)
        .where(FundamentalData.stock_id == stock_id)
        .order_by(FundamentalData.period_year.desc(), FundamentalData.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    # Ambil sektor saham
    stock: Stock | None = db.execute(
        select(Stock).where(Stock.id == stock_id)
    ).scalar_one_or_none()

    sector_metrics: SectorMetrics | None = None
    if stock and stock.sector:
        from datetime import date
        sector_metrics = db.execute(
            select(SectorMetrics)
            .where(SectorMetrics.sector == stock.sector)
            .order_by(SectorMetrics.calculated_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    # Hitung komponen
    valuation_score: float | None = None
    quality_score: float | None = None
    momentum_score: float | None = None

    if fund is not None:
        valuation_score = calculate_valuation_score(fund, sector_metrics)
        quality_score = calculate_quality_score(fund)

    momentum_score = calculate_momentum_score(stock_id, db)

    # Gabungkan dengan bobot 40/40/20
    available: list[tuple[float | None, float]] = [
        (valuation_score, 0.4),
        (quality_score, 0.4),
        (momentum_score, 0.2),
    ]

    present = [(s, w) for s, w in available if s is not None]
    is_partial = len(present) < len(available)

    if not present:
        # Tidak ada data sama sekali — kembalikan skor 0
        total_score = 0.0
        is_partial = True
    else:
        total_weight = sum(w for _, w in present)
        total_score = _clamp(sum(s * w for s, w in present) / total_weight)

    recommendation = determine_recommendation(total_score)

    # Bangun score_factors
    score_factors: dict = {
        "valuation": {
            "score": round(valuation_score, 2) if valuation_score is not None else None,
            "weight": 0.4,
            "available": valuation_score is not None,
        },
        "quality": {
            "score": round(quality_score, 2) if quality_score is not None else None,
            "weight": 0.4,
            "available": quality_score is not None,
        },
        "momentum": {
            "score": round(momentum_score, 2) if momentum_score is not None else None,
            "weight": 0.2,
            "available": momentum_score is not None,
        },
    }

    return {
        "score": round(total_score, 2),
        "valuation_score": round(valuation_score, 2) if valuation_score is not None else None,
        "quality_score": round(quality_score, 2) if quality_score is not None else None,
        "momentum_score": round(momentum_score, 2) if momentum_score is not None else None,
        "is_partial": is_partial,
        "recommendation": recommendation,
        "score_factors": score_factors,
    }
