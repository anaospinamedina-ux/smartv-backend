import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import create_access_token
from database import Base, engine, get_db, SessionLocal
from routers import hub, tv, reminders as reminders_router
from scheduler import load_reminders, scheduler

logging.basicConfig(level=logging.INFO)

CAREGIVER_PASSWORD = os.getenv("CAREGIVER_PASSWORD", "change-me")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        load_reminders(db)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="SmartV API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hub.router)
app.include_router(tv.router)
app.include_router(reminders_router.router)


class LoginRequest(BaseModel):
    password: str


@app.post("/auth/login")
def login(body: LoginRequest):
    if body.password != CAREGIVER_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    token = create_access_token(sub="caregiver")
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health")
def health():
    return {"status": "ok"}
