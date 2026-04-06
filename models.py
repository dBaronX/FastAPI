#  apps/services-fastapi/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String)
    telegram_id = Column(String, unique=True, nullable=True)
    subscription_tier = Column(String)
    balance = Column(Float, default=0)

class Ad(Base):
    __tablename__ = "ads"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_url = Column(String)
    reward_amount = Column(Float)
    priority = Column(Integer)
    daily_budget = Column(Float)
    total_budget = Column(Float)
    expires_at = Column(DateTime)
    status = Column(String)

class AdView(Base):
    __tablename__ = "ad_views"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))
    viewed_at = Column(DateTime, default=datetime.utcnow)
    earned_amount = Column(Float)