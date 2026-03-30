"""APScheduler setup for BEI Stock Dashboard background jobs."""

import logging
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.services.data_pipeline import (
    fetch_corporate_actions,
    fetch_daily_ohlcv,
    fetch_fundamental_data,
    fetch_intraday_prices,
)
from app.services.sector_metrics_service import calculate_sector_metrics

logger = logging.getLogger(__name__)

WIB = pytz.timezone("Asia/Jakarta")

_scheduler: BackgroundScheduler | None = None


# ---------------------------------------------------------------------------
# Job wrappers — each creates its own DB session
# ---------------------------------------------------------------------------

def _job_intraday_prices() -> None:
    """Fetch intraday prices — runs every 15 min on trading days 09:00–16:30 WIB."""
    now_wib = datetime.now(WIB)
    # Guard: only run Mon–Fri (weekday 0–4)
    if now_wib.weekday() > 4:
        return
    # Guard: only between 09:00 and 16:30
    start = now_wib.replace(hour=9, minute=0, second=0, microsecond=0)
    end = now_wib.replace(hour=16, minute=30, second=0, microsecond=0)
    if not (start <= now_wib <= end):
        return

    logger.info("[scheduler] Running intraday price fetch.")
    db = SessionLocal()
    try:
        fetch_intraday_prices(db)
    except Exception as exc:
        logger.error("[scheduler] intraday prices job failed: %s", exc)
    finally:
        db.close()


def _job_daily_ohlcv() -> None:
    """Fetch daily OHLCV — runs every day at 17:00 WIB."""
    logger.info("[scheduler] Running daily OHLCV fetch.")
    db = SessionLocal()
    try:
        fetch_daily_ohlcv(db)
    except Exception as exc:
        logger.error("[scheduler] daily OHLCV job failed: %s", exc)
    finally:
        db.close()


def _job_fundamental_data() -> None:
    """Fetch fundamental data — runs every day at 06:00 WIB."""
    logger.info("[scheduler] Running fundamental data fetch.")
    db = SessionLocal()
    try:
        fetch_fundamental_data(db)
    except Exception as exc:
        logger.error("[scheduler] fundamental data job failed: %s", exc)
    finally:
        db.close()


def _job_sector_metrics() -> None:
    """Calculate sector metrics — runs every day at 17:30 WIB."""
    logger.info("[scheduler] Running sector metrics calculation.")
    db = SessionLocal()
    try:
        calculate_sector_metrics(db)
    except Exception as exc:
        logger.error("[scheduler] sector metrics job failed: %s", exc)
    finally:
        db.close()


def _job_score_calculation() -> None:
    """Run scoring job — runs every day at 17:00 WIB."""
    logger.info("[scheduler] Running score calculation job.")
    try:
        # Import here to avoid circular imports; score_worker is implemented in Task 6.2
        from app.workers.score_worker import run_scoring_job  # noqa: PLC0415

        db = SessionLocal()
        try:
            run_scoring_job(db)
        finally:
            db.close()
    except ImportError:
        logger.warning("[scheduler] score_worker.run_scoring_job not yet implemented, skipping.")
    except Exception as exc:
        logger.error("[scheduler] score calculation job failed: %s", exc)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """Create and start the APScheduler BackgroundScheduler."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("[scheduler] Scheduler already running.")
        return

    _scheduler = BackgroundScheduler(timezone=WIB)

    # Intraday prices: every 15 minutes, Mon–Fri, 09:00–16:30 WIB
    # The job itself guards the time window; cron fires every 15 min all day
    # but the guard inside _job_intraday_prices restricts execution.
    _scheduler.add_job(
        _job_intraday_prices,
        CronTrigger(
            day_of_week="mon-fri",
            hour="9-16",
            minute="0,15,30,45",
            timezone=WIB,
        ),
        id="intraday_prices",
        name="Intraday Price Fetch (15 min, trading hours)",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Daily OHLCV: every day at 17:00 WIB
    _scheduler.add_job(
        _job_daily_ohlcv,
        CronTrigger(hour=17, minute=0, timezone=WIB),
        id="daily_ohlcv",
        name="Daily OHLCV Fetch",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Score calculation: every day at 17:00 WIB (runs alongside OHLCV)
    _scheduler.add_job(
        _job_score_calculation,
        CronTrigger(hour=17, minute=0, timezone=WIB),
        id="score_calculation",
        name="Score Calculation",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Fundamental data: every day at 06:00 WIB
    _scheduler.add_job(
        _job_fundamental_data,
        CronTrigger(hour=6, minute=0, timezone=WIB),
        id="fundamental_data",
        name="Fundamental Data Fetch",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Sector metrics: every day at 17:30 WIB
    _scheduler.add_job(
        _job_sector_metrics,
        CronTrigger(hour=17, minute=30, timezone=WIB),
        id="sector_metrics",
        name="Sector Metrics Calculation",
        replace_existing=True,
        misfire_grace_time=600,
    )

    _scheduler.start()
    logger.info("[scheduler] APScheduler started with %d jobs.", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Stop the APScheduler gracefully."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] APScheduler stopped.")
    _scheduler = None
