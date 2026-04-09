import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import stripe
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client

# =========================================
# ENV
# =========================================
NODE_ENV = os.getenv("NODE_ENV", "development")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SITE_URL = os.getenv("SITE_URL_PROD", "https://dbaronx.com")

STRIPE_SECRET = (
    os.getenv("STRIPE_SECRET_KEY_LIVE", "")
    if NODE_ENV == "production"
    else os.getenv("STRIPE_SECRET_KEY_TEST", "")
)

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="dBaronX FastAPI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# MODELS
# =========================================
class ConfirmAdRequest(BaseModel):
    ad_id: str = Field(..., description="Ad video ID")


class CreatePaymentRequest(BaseModel):
    order_id: str = Field(..., description="Order ID in Supabase")


# =========================================
# HELPERS
# =========================================
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_by_telegram_id(telegram_id: str) -> Dict[str, Any]:
    result = (
        supabase.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return result.data[0]


def get_affiliate_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    result = (
        supabase.table("affiliates")
        .select("*, subscription_tier_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def get_subscription_tier_by_id(subscription_tier_id: Optional[str]) -> Dict[str, Any]:
    if not subscription_tier_id:
        result = (
            supabase.table("subscription_tiers")
            .select("*")
            .eq("code", "free")
            .limit(1)
            .execute()
        )
        if not result.data:
            return {
                "code": "free",
                "watch_min_seconds": 30,
                "reward_multiplier": 1.0,
                "daily_ads_limit": 5,
            }
        return result.data[0]

    result = (
        supabase.table("subscription_tiers")
        .select("*")
        .eq("id", subscription_tier_id)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return {
        "code": "free",
        "watch_min_seconds": 30,
        "reward_multiplier": 1.0,
        "daily_ads_limit": 5,
    }


def get_user_tier_settings(user_id: str) -> Dict[str, Any]:
    affiliate = get_affiliate_for_user(user_id)
    tier = get_subscription_tier_by_id(
        affiliate["subscription_tier_id"] if affiliate else None
    )

    return {
        "code": tier.get("code", "free"),
        "watch_min_seconds": int(tier.get("watch_min_seconds", 30) or 30),
        "reward_multiplier": float(tier.get("reward_multiplier", 1.0) or 1.0),
        "daily_ads_limit": int(tier.get("daily_ads_limit", 5) or 5),
    }


def get_utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def get_today_watch_count(user_id: str) -> int:
    result = (
        supabase.table("ad_watches")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("utc_watch_date", get_utc_date())
        .eq("reward_status", "earned")
        .execute()
    )
    return int(result.count or 0)


def get_available_ads_for_user(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    tier = get_user_tier_settings(user["id"])
    watched_today = get_today_watch_count(user["id"])

    if watched_today >= tier["daily_ads_limit"]:
        return []

    watched_result = (
        supabase.table("ad_watches")
        .select("ad_video_id")
        .eq("user_id", user["id"])
        .eq("utc_watch_date", get_utc_date())
        .eq("reward_status", "earned")
        .execute()
    )

    watched_ids = [row["ad_video_id"] for row in watched_result.data] if watched_result.data else []

    query = (
        supabase.table("ad_videos")
        .select("*")
        .eq("status", "active")
        .order("geo_priority", desc=True)
        .order("created_at", desc=False)
        .limit(20)
    )

    result = query.execute()
    ads = result.data or []

    filtered_ads = []
    for ad in ads:
        if ad["id"] in watched_ids:
            continue

        reward_amount = float(ad.get("reward_amount", 0) or 0)
        filtered_ads.append(
            {
                "id": ad["id"],
                "title": ad.get("title"),
                "description": ad.get("description"),
                "thumbnail_url": ad.get("thumbnail_url"),
                "video_url": ad.get("video_url"),
                "category": ad.get("category"),
                "country": ad.get("country"),
                "city": ad.get("city"),
                "reward_amount": round(reward_amount * tier["reward_multiplier"], 2),
                "reward_currency": ad.get("reward_currency", "USD"),
                "min_watch_seconds": int(
                    ad.get("min_watch_seconds_override") or tier["watch_min_seconds"]
                ),
                "duration_seconds": ad.get("duration_seconds", 0),
                "tier_code": tier["code"],
                "ads_remaining_today": max(tier["daily_ads_limit"] - watched_today, 0),
            }
        )

    return filtered_ads


def create_ad_watch_record(user_id: str, ad: Dict[str, Any], required_watch_seconds: int) -> Dict[str, Any]:
    insert_payload = {
        "user_id": user_id,
        "ad_video_id": ad["id"],
        "watch_started_at": now_iso(),
        "required_watch_seconds": required_watch_seconds,
        "reward_amount": ad.get("reward_amount", 0),
        "reward_currency": ad.get("reward_currency", "USD"),
        "reward_status": "pending",
        "validation_status": "pending",
        "utc_watch_date": get_utc_date(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    result = supabase.table("ad_watches").insert(insert_payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create watch record")
    return result.data[0]


def get_latest_pending_watch(user_id: str, ad_id: str) -> Dict[str, Any]:
    result = (
        supabase.table("ad_watches")
        .select("*")
        .eq("user_id", user_id)
        .eq("ad_video_id", ad_id)
        .eq("utc_watch_date", get_utc_date())
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=400, detail="No watch session found")

    return result.data[0]


def update_user_balance(user: Dict[str, Any], reward: float) -> None:
    current_balance = float(user.get("balance", 0) or 0)
    new_balance = current_balance + reward

    result = (
        supabase.table("users")
        .update(
            {
                "balance": new_balance,
                "updated_at": now_iso(),
            }
        )
        .eq("id", user["id"])
        .execute()
    )

    if result.data is None:
        raise HTTPException(status_code=500, detail="Failed to update user balance")


def record_affiliate_earning(user_id: str, affiliate_id: Optional[str], ad_id: str, amount: float, currency: str) -> None:
    payload = {
        "affiliate_id": affiliate_id,
        "user_id": user_id,
        "source_type": "ad_watch",
        "source_id": ad_id,
        "amount": amount,
        "currency": currency,
        "status": "earned",
        "description": "Reward from ad watch",
        "earned_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    supabase.table("affiliate_earnings").insert(payload).execute()


def get_order_by_id(order_id: str) -> Dict[str, Any]:
    result = (
        supabase.table("orders")
        .select("*")
        .eq("id", order_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Order not found")
    return result.data[0]


# =========================================
# ROUTES
# =========================================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "fastapi-core",
        "timestamp": now_iso(),
    }


@app.get("/ads")
async def get_ads(telegram_id: str = Header(...)):
    user = get_user_by_telegram_id(telegram_id)
    ads = get_available_ads_for_user(user)
    return {
        "status": "success",
        "ads": ads,
    }


@app.post("/watch/start")
async def start_watch(data: ConfirmAdRequest, telegram_id: str = Header(...)):
    user = get_user_by_telegram_id(telegram_id)
    ads = get_available_ads_for_user(user)

    ad = next((item for item in ads if str(item["id"]) == str(data.ad_id)), None)
    if not ad:
      raise HTTPException(status_code=404, detail="Ad not available for this user")

    watch = create_ad_watch_record(
        user_id=user["id"],
        ad=ad,
        required_watch_seconds=ad["min_watch_seconds"],
    )

    return {
        "status": "started",
        "watch_id": watch["id"],
        "ad_id": ad["id"],
        "required_watch_seconds": ad["min_watch_seconds"],
    }


@app.post("/confirm")
async def confirm_ad(data: ConfirmAdRequest, telegram_id: str = Header(...)):
    user = get_user_by_telegram_id(telegram_id)
    tier = get_user_tier_settings(user["id"])

    watch = get_latest_pending_watch(user["id"], data.ad_id)

    watch_started_at = datetime.fromisoformat(
        watch["watch_started_at"].replace("Z", "+00:00")
    )
    elapsed = (datetime.now(timezone.utc) - watch_started_at).total_seconds()

    required_watch_seconds = int(
        watch.get("required_watch_seconds") or tier["watch_min_seconds"]
    )
    if elapsed < required_watch_seconds:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum watch time not reached. Required: {required_watch_seconds}s",
        )

    reward_amount = float(watch.get("reward_amount", 0) or 0)
    reward_currency = watch.get("reward_currency", "USD")

    update_watch = (
        supabase.table("ad_watches")
        .update(
            {
                "watch_completed_at": now_iso(),
                "watched_seconds": int(elapsed),
                "captcha_verified": True,
                "reward_status": "earned",
                "validation_status": "approved",
                "updated_at": now_iso(),
            }
        )
        .eq("id", watch["id"])
        .execute()
    )

    if update_watch.data is None:
        raise HTTPException(status_code=500, detail="Failed to finalize watch")

    update_user_balance(user, reward_amount)

    affiliate = get_affiliate_for_user(user["id"])
    record_affiliate_earning(
        user_id=user["id"],
        affiliate_id=affiliate["id"] if affiliate else None,
        ad_id=str(data.ad_id),
        amount=reward_amount,
        currency=reward_currency,
    )

    return {
        "status": "success",
        "earned": reward_amount,
        "currency": reward_currency,
        "watch_id": watch["id"],
    }


@app.get("/products")
async def get_products():
    result = (
        supabase.table("products")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "status": "success",
        "products": result.data or [],
    }


@app.post("/payment/confirm")
async def confirm_payment(req: CreatePaymentRequest):
    order = get_order_by_id(req.order_id)

    update = (
        supabase.table("orders")
        .update(
            {
                "payment_status": "paid",
                "status": "paid",
                "paid_at": now_iso(),
                "updated_at": now_iso(),
            }
        )
        .eq("id", order["id"])
        .execute()
    )

    if update.data is None:
        raise HTTPException(status_code=500, detail="Failed to confirm payment")

    return {"ok": True, "order_id": order["id"]}