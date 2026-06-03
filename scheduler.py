import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from hub_manager import hub_manager
from models import Reminder

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _fire_reminder(reminder_id: int, text: str):
    sent = await hub_manager.send_command({"type": "remind", "text": text})
    if not sent:
        logger.warning("Hub not connected — reminder '%s' could not be delivered", text)


def schedule_reminder(reminder: Reminder):
    job_id = f"reminder_{reminder.id}"

    if reminder.repeat == "daily":
        trigger = CronTrigger(
            hour=reminder.datetime_utc.hour,
            minute=reminder.datetime_utc.minute,
            start_date=reminder.datetime_utc,
        )
    elif reminder.repeat == "weekly":
        trigger = CronTrigger(
            day_of_week=reminder.datetime_utc.weekday(),
            hour=reminder.datetime_utc.hour,
            minute=reminder.datetime_utc.minute,
            start_date=reminder.datetime_utc,
        )
    else:
        if reminder.datetime_utc <= datetime.utcnow():
            return
        trigger = DateTrigger(run_date=reminder.datetime_utc)

    scheduler.add_job(
        _fire_reminder,
        trigger=trigger,
        args=[reminder.id, reminder.label],
        id=job_id,
        replace_existing=True,
    )


def unschedule_reminder(reminder_id: int):
    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def load_reminders(db: Session):
    reminders = db.query(Reminder).filter(Reminder.active == True).all()
    for r in reminders:
        schedule_reminder(r)
    logger.info("Loaded %d reminder(s) from database", len(reminders))
