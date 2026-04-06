#  apps/services-fastapi/main.py

import os
import asyncio
import stripe
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from supabase import create_client
from pydantic import BaseModel
from models import Base, User, Ad, AdView
from database import get_db, engine
from ai_router import generate_story
from schemas import ConfirmAdRequest

stripe.api_key = os.getenv("STRIPE_SECRET_KEY_LIVE") if os.getenv("NODE_ENV") == "production" else os.getenv("STRIPE_SECRET_KEY_TEST")

app = FastAPI(title="dBaronX Services")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dbaronx.com", "https://*.onrender.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# HCAPTCHA
async def verify_hcaptcha(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Captcha token required")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.hcaptcha.com/siteverify",   # Official endpoint
            data={
                "secret": os.getenv("HCAPTCHA_SECRET"),
                "response": token,
                # "remoteip": request.client.host   # optional but recommended
            }
        )
        data = resp.json()

    if not data.get("success", False):
        raise HTTPException(status_code=400, detail="Captcha failed")

    return True

#hcaptcha 
@app.post("/confirm")
async def confirm_ad(data: ConfirmAdRequest, telegram_id: str = Header(None), db: Session = Depends(get_db)):
    user = await get_user_by_telegram(telegram_id, db)
    
    if not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="Captcha failed")

    # ... rest of your reward logic
# TELEGRAM DEPENDENCY
async def get_user_by_telegram(telegram_id: str = Header(None), db: Session = Depends(get_db)):
    if not telegram_id:
        raise HTTPException(401, "telegram_id header required")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

# ADS ENDPOINTS (from affiliate)
@app.get("/ads")
async def fetch_ads(telegram_id: str = Header(None), db: Session = Depends(get_db)):
    user = await get_user_by_telegram(telegram_id, db)
    # your get_ads_for_user logic here (from previous response)
    return get_ads_for_user(db, user)

@app.post("/confirm")
async def confirm_ad(data: ConfirmAdRequest, telegram_id: str = Header(None), db: Session = Depends(get_db)):
    user = await get_user_by_telegram(telegram_id, db)
    if not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="Captcha failed")
    success = reward_user(db, user.id, data.ad_id)
    if not success:
        raise HTTPException(400, "Reward failed")
    return {"status": "success"}    

# STRIPE WEBHOOK (central for ALL payments)
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET"))
    except Exception:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Handle presale, dreams, Medusa orders, etc.
        order_id = session.get("metadata", {}).get("orderId")
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        supabase.table("presale_commitments").update({"status": "paid"}).eq("id", order_id).execute()
        # Add similar for dreams, orders, etc.

    return {"received": True}

# AI STORY (tiered)
@app.post("/ai/story")
async def ai_story(req: Request, db: Session = Depends(get_db)):
    data = await req.json()
    user = await get_user_by_telegram(data.get("telegram_id"), db)  # or JWT
    # Tier logic in ai_router
    result = generate_story(data["prompt"], user.subscription_tier)
    return result

# ... add /dreams, /presale etc. from previous screenshots

@app.on_event("startup")
async def startup():
    asyncio.create_task(reset_daily_budgets())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))