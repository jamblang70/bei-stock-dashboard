"""Score Worker — menjalankan scoring engine untuk semua emiten aktif."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis
from app.models.stock import Stock, StockScore
from app.services.scoring_engine import calculate_score
from app.services.sector_metrics_service import calculate_sector_metrics

logger = logging.getLogger(__name__)


def run_scoring_job(db: Session) -> None:
    """
    Jalankan scoring untuk semua emiten aktif.

    Langkah:
    1. Ambil semua saham aktif.
    2. Untuk setiap saham, hitung skor via calculate_score().
    3. Insert baris baru ke stock_scores (history tetap terjaga).
    4. Hitung ulang sector_metrics.
    5. Invalidate Redis cache: stock:score:{code} dan stock:profile:{code}.
    """
    stocks = list(
        db.execute(select(Stock).where(Stock.is_active == True))  # noqa: E712
        .scalars()
        .all()
    )

    if not stocks:
        logger.warning("Tidak ada emiten aktif ditemukan.")
        return

    logger.info("Memulai scoring untuk %d emiten.", len(stocks))

    redis = get_redis()
    calculated_at = datetime.now(tz=timezone.utc)
    processed = 0
    errors = 0

    for stock in stocks:
        try:
            result = calculate_score(stock.id, db)

            score_row = StockScore(
                stock_id=stock.id,
                score=result["score"],
                valuation_score=result["valuation_score"],
                quality_score=result["quality_score"],
                momentum_score=result["momentum_score"],
                is_partial=result["is_partial"],
                recommendation=result["recommendation"],
                score_factors=result["score_factors"],
                calculated_at=calculated_at,
            )
            db.add(score_row)
            db.flush()  # flush per saham agar error terisolasi

            # Invalidate Redis cache
            try:
                redis.delete(f"stock:score:{stock.code}")
                redis.delete(f"stock:profile:{stock.code}")
            except Exception as redis_err:
                logger.warning(
                    "Gagal invalidate cache untuk %s: %s", stock.code, redis_err
                )

            processed += 1

        except Exception as exc:
            db.rollback()
            errors += 1
            logger.error("Error scoring %s: %s", stock.code, exc)
            continue

        if processed % 10 == 0:
            logger.info("Progress: %d/%d emiten diproses.", processed, len(stocks))

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Gagal commit batch score: %s", exc)
        raise

    logger.info(
        "Scoring selesai. Berhasil: %d, Gagal: %d.", processed, errors
    )

    # Hitung ulang sector metrics setelah semua skor tersimpan
    try:
        calculate_sector_metrics(db)
        logger.info("Sector metrics berhasil diperbarui.")
    except Exception as exc:
        logger.error("Gagal menghitung sector metrics: %s", exc)
