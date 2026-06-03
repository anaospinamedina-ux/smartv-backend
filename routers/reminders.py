from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from models import Reminder
from scheduler import schedule_reminder, unschedule_reminder

router = APIRouter(prefix="/reminders", tags=["reminders"])


class ReminderCreate(BaseModel):
    label: str
    datetime_utc: datetime
    repeat: Optional[str] = None  # "daily" | "weekly" | None


class ReminderOut(BaseModel):
    id: int
    label: str
    datetime_utc: datetime
    repeat: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db), _: str = Depends(verify_token)):
    return db.query(Reminder).filter(Reminder.active == True).order_by(Reminder.datetime_utc).all()


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(
    body: ReminderCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    if body.repeat not in (None, "daily", "weekly"):
        raise HTTPException(status_code=400, detail="repeat must be 'daily', 'weekly', or null")

    reminder = Reminder(
        label=body.label,
        datetime_utc=body.datetime_utc,
        repeat=body.repeat,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    schedule_reminder(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.active = False
    db.commit()
    unschedule_reminder(reminder_id)
