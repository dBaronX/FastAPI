from sqlalchemy.orm import Session
from models import Ad, AdView
from datetime import datetime
import random

TIERS = {
    "free": 5,
    "basic": 15,
    "pro": 40
}

def get_ads_for_user(db: Session, user):
    today = datetime.utcnow().date()

    viewed_ids = db.query(AdView.ad_id).filter(
        AdView.user_id == user["sub"],
        AdView.viewed_at >= today
    ).all()

    viewed_ids = [v[0] for v in viewed_ids]

    ads = db.query(Ad).filter(
        Ad.status == "active",
        Ad.expires_at > datetime.utcnow(),
        Ad.daily_budget > 0
    ).all()

    ads = [ad for ad in ads if ad.id not in viewed_ids]

    ads.sort(key=lambda x: random.random() * x.priority)

    return ads[:TIERS.get(user["tier"], 5)]