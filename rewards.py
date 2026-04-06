from sqlalchemy.orm import Session
from models import AdView, Ad, User
from datetime import datetime

def reward_user(db: Session, user_id, ad_id):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    user = db.query(User).filter(User.id == user_id).first()

    if not ad or not user:
        return False

    if ad.daily_budget <= 0:
        return False

    view = AdView(
        user_id=user_id,
        ad_id=ad_id,
        earned_amount=ad.reward_amount
    )

    user.balance += ad.reward_amount
    ad.daily_budget -= ad.reward_amount
    ad.total_budget -= ad.reward_amount

    db.add(view)
    db.commit()

    return True