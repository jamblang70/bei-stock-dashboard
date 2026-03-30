"""AI Worker — menjalankan analisa AI untuk emiten BEI."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.redis_client import get_redis
from app.models.stock import Stock
from app.services.ai_analyzer import run_ai_analysis

logger = logging.getLogger(__name__)


def run_ai_job_for_stock(stock_id: int) -> None:
    """
    Jalankan analisa AI untuk satu emiten.

    Membuat DB session sendiri, memanggil run_ai_analysis,
    lalu invalidate Redis cache ai_analysis:{stock_code}.
    """
    db: Session = SessionLocal()
    try:
        # Ambil kode saham untuk cache invalidation
        stock = db.execute(
            select(Stock).where(Stock.id == stock_id)
        ).scalar_one_or_none()

        if stock is None:
            logger.error("Stock id=%d tidak ditemukan, skip.", stock_id)
            return

        logger.info("Memulai analisa AI untuk %s (id=%d).", stock.code, stock_id)
        analysis = run_ai_analysis(db, stock_id)

        # Invalidate Redis cache
        try:
            redis = get_redis()
            redis.delete(f"ai_analysis:{stock.code}")
            logger.debug("Cache ai_analysis:%s dihapus.", stock.code)
        except Exception as redis_err:
            logger.warning("Gagal invalidate cache untuk %s: %s", stock.code, redis_err)

        logger.info(
            "Analisa AI selesai untuk %s — rekomendasi: %s, model: %s.",
            stock.code,
            analysis.recommendation,
            analysis.model_used,
        )

    except Exception as exc:
        logger.error("Error analisa AI untuk stock_id=%d: %s", stock_id, exc)
        raise
    finally:
        db.close()


def run_ai_job_for_all(db: Session) -> None:
    """
    Jalankan analisa AI untuk semua emiten aktif.

    Error per emiten ditangani secara individual agar tidak menghentikan proses.
    Cache di-invalidate setelah setiap analisa berhasil.
    """
    stocks = list(
        db.execute(select(Stock).where(Stock.is_active == True))  # noqa: E712
        .scalars()
        .all()
    )

    if not stocks:
        logger.warning("Tidak ada emiten aktif ditemukan.")
        return

    logger.info("Memulai analisa AI untuk %d emiten.", len(stocks))

    redis = get_redis()
    processed = 0
    errors = 0

    for stock in stocks:
        try:
            analysis = run_ai_analysis(db, stock.id)

            # Invalidate Redis cache
            try:
                redis.delete(f"ai_analysis:{stock.code}")
            except Exception as redis_err:
                logger.warning(
                    "Gagal invalidate cache untuk %s: %s", stock.code, redis_err
                )

            processed += 1
            logger.debug(
                "Analisa AI selesai untuk %s — rekomendasi: %s.",
                stock.code,
                analysis.recommendation,
            )

        except Exception as exc:
            errors += 1
            logger.error("Error analisa AI untuk %s: %s", stock.code, exc)
            continue

        if processed % 10 == 0:
            logger.info("Progress AI: %d/%d emiten diproses.", processed, len(stocks))

    logger.info(
        "Analisa AI selesai. Berhasil: %d, Gagal: %d.", processed, errors
    )
