"""Analysis API — endpoint untuk AI analysis saham."""

import json
import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.ai_analysis import AIAnalysis
from app.models.stock import Stock
from app.schemas.analysis import AIAnalysisRefreshResponse, AIAnalysisResponse
from app.workers.ai_worker import run_ai_job_for_stock

logger = logging.getLogger(__name__)

router = APIRouter()

AI_CACHE_TTL = 6 * 3600       # 6 jam dalam detik
REFRESH_RATE_LIMIT_TTL = 300   # 5 menit dalam detik


def _get_stock_or_404(code: str, db: Session) -> Stock:
    stock = db.execute(
        select(Stock).where(Stock.code == code.upper())
    ).scalar_one_or_none()
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saham dengan kode '{code}' tidak ditemukan.",
        )
    return stock


@router.get("/{code}/ai", response_model=AIAnalysisResponse)
def get_ai_analysis(code: str, db: Session = Depends(get_db)):
    """
    Ambil hasil analisa AI terbaru untuk saham {code}.

    Cek Redis cache terlebih dahulu (key: ai_analysis:{code}, TTL 6 jam).
    Jika tidak ada di cache, ambil dari DB dan simpan ke cache.
    """
    stock = _get_stock_or_404(code, db)
    cache_key = f"ai_analysis:{stock.code}"

    # Cek Redis cache
    try:
        redis = get_redis()
        cached = redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return AIAnalysisResponse(**data)
    except Exception as redis_err:
        logger.warning("Redis error saat get cache %s: %s", cache_key, redis_err)

    # Ambil dari DB
    analysis = db.execute(
        select(AIAnalysis)
        .where(AIAnalysis.stock_id == stock.id)
        .order_by(AIAnalysis.generated_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Belum ada analisa AI untuk saham '{code}'. "
                f"Gunakan POST /{code}/ai/refresh untuk memulai analisa."
            ),
        )

    response = AIAnalysisResponse.model_validate(analysis)

    # Simpan ke Redis cache
    try:
        redis = get_redis()
        redis.setex(cache_key, AI_CACHE_TTL, response.model_dump_json())
    except Exception as redis_err:
        logger.warning("Redis error saat set cache %s: %s", cache_key, redis_err)

    return response


@router.post("/{code}/ai/refresh", response_model=AIAnalysisRefreshResponse)
def refresh_ai_analysis(code: str, db: Session = Depends(get_db)):
    """
    Trigger ulang analisa AI untuk saham {code}.

    Rate-limited: maksimal 1x per 5 menit per saham via Redis.
    """
    stock = _get_stock_or_404(code, db)
    rate_key = f"ai_refresh_lock:{stock.code}"

    # Cek rate limit
    try:
        redis = get_redis()
        if redis.exists(rate_key):
            ttl = redis.ttl(rate_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Analisa baru sudah diminta. Coba lagi dalam {ttl} detik.",
            )
        # Set lock sebelum memulai
        redis.setex(rate_key, REFRESH_RATE_LIMIT_TTL, "1")
    except HTTPException:
        raise
    except Exception as redis_err:
        logger.warning("Redis error saat cek rate limit %s: %s", rate_key, redis_err)

    # Jalankan analisa di background (fire-and-forget via thread)
    stock_id = stock.id
    stock_code = stock.code

    def _run():
        try:
            run_ai_job_for_stock(stock_id)
        except Exception as exc:
            logger.error("Background AI job gagal untuk %s: %s", stock_code, exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    logger.info("Analisa AI di-trigger untuk %s.", stock_code)
    return AIAnalysisRefreshResponse(
        message=(
            f"Analisa AI untuk {stock_code} sedang diproses. "
            "Hasil akan tersedia dalam beberapa saat."
        ),
        stock_code=stock_code,
    )
