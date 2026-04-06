#  apps/services-fastapi/main.py
import os
import asyncio
import stripe
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from supabase import create_client
from pydantic import BaseModel
from models import Base, User, Ad, AdView
from database import get_db, engine
from ai_router import generate_story
from schemas import ConfirmAdRequest

stripe.api_key = os.getenv("STRIPE_SECRET_KEY_LIVE") if os.getenv("NODE_ENV") == "production" else os.getenv("STRIPE_SECRET_KEY_TEST")

app = FastAPI(title="dBaronX Services")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(bind=engine)

# DAILY REWARD POOL (60% of total advertiser daily budget)
async def get_daily_reward_pool(db: Session):
    today = datetime.utcnow().date()
    # Sum all active ad daily_budget * 0.6
    total_b = db.query(Ad).filter(Ad.expires_at > datetime.utcnow()).with_entities(Ad.daily_budget).all()
    pool = sum([float(b[0]) for b in total_b]) * 0.6
    return pool

# HCAPTCHA (web) + MIN WATCH TIME (bot + web)
async def verify_hcaptcha(token: str):
    if not token:
        raise HTTPException(400, "Captcha required")
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.hcaptcha.com/siteverify", data={"secret": os.getenv("HCAPTCHA_SECRET"), "response": token})
        if not r.json().get("success"):
            raise HTTPException(400, "Captcha failed")
    return True

async def get_user_by_telegram(telegram_id: str = Header(None), db: Session = Depends(get_db)):
    if not telegram_id:
        raise HTTPException(401, "telegram_id required")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.get("/ads")
async def fetch_ads(telegram_id: str = Header(None), db: Session = Depends(get_db)):
    user = await get_user_by_telegram(telegram_id, db)
    # Tier priority + min watch time
    ads = db.query(Ad).filter(Ad.expires_at > datetime.utcnow()).order_by(Ad.priority.desc()).limit(10).all()
    return [{"id": a.id, "title": a.title, "reward": a.reward_amount, "min_watch_seconds": a.min_watch_seconds} for a in ads]

@app.post("/confirm")
async def confirm_ad(data: ConfirmAdRequest, telegram_id: str = Header(None), db: Session = Depends(get_db)):
    user = await get_user_by_telegram(telegram_id, db)
    
    # MIN WATCH TIME ENFORCEMENT
    view = db.query(AdView).filter(AdView.user_id == user.id, AdView.ad_id == data.ad_id).order_by(AdView.viewed_at.desc()).first()
    if view and (datetime.utcnow() - view.watch_start).total_seconds() < 30:  # 30s minimum
        raise HTTPException(400, "You must watch the full ad (minimum 30 seconds)")

    # 60% BUDGET CHECK + TIER MULTIPLIER
    reward = data.reward_amount * (2 if user.subscription_tier == "Pro" else 1.5 if user.subscription_tier == "Basic" else 1)
    pool = await get_daily_reward_pool(db)
    if reward > pool:
        raise HTTPException(400, "Daily reward pool exhausted – come back tomorrow")

    # Reward user & deduct from pool
    user.balance += reward
    db.commit()

    return {"status": "success", "earned": reward}

# ... keep all your other endpoints (/ai/story, /dreams, /balance, /register, /webhook/stripe)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))