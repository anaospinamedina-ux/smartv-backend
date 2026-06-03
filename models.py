from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    datetime_utc = Column(DateTime, nullable=False)
    repeat = Column(String, nullable=True)  # "daily" | "weekly" | None
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
