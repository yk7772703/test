"""
APScheduler jobs: daily sanctions update, regulatory feed refresh.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler(db_factory):
    from app.services.sanctions_service import run_daily_update
    from app.services.regulatory_service import fetch_regulatory_updates

    async def _daily_sanctions():
        logger.info("Daily sanctions update started")
        db = next(db_factory())
        try:
            results = await run_daily_update(db)
            logger.info("Sanctions update done: %s", results)
        except Exception as e:
            logger.error("Sanctions update failed: %s", e)
        finally:
            db.close()

    async def _regulatory_refresh():
        logger.info("Regulatory feed refresh started")
        db = next(db_factory())
        try:
            await fetch_regulatory_updates(db)
        except Exception as e:
            logger.error("Regulatory refresh failed: %s", e)
        finally:
            db.close()

    # Daily at 06:00 UTC
    scheduler.add_job(_daily_sanctions, CronTrigger(hour=6, minute=0), id="daily_sanctions")
    # Every 4 hours for regulatory feed
    scheduler.add_job(_regulatory_refresh, CronTrigger(hour="*/4"), id="regulatory_refresh")

    scheduler.start()
    logger.info("Scheduler started")
