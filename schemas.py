from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# =========================
# USER
# =========================

class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    subscription_tier: str
    balance: float

    class Config:
        from_attributes = True


# =========================
# ADS
# =========================

class AdBase(BaseModel):
    title: str
    video_url: str
    reward_amount: float
    priority: int


class AdCreate(AdBase):
    daily_budget: float
    total_budget: float
    expires_at: datetime


class AdResponse(AdBase):
    id: int
    status: str
    daily_budget: float
    total_budget: float
    expires_at: datetime

    class Config:
        from_attributes = True


# =========================
# AD VIEW (TRACKING)
# =========================

class AdViewResponse(BaseModel):
    id: int
    user_id: str
    ad_id: int
    viewed_at: datetime
    earned_amount: float

    class Config:
        from_attributes = True


# =========================
# CONFIRM AD REQUEST
# =========================

class ConfirmAdRequest(BaseModel):
    ad_id: int
    captcha_token: str


# =========================
# WALLET / EARNINGS
# =========================

class BalanceResponse(BaseModel):
    balance: float


# =========================
# WITHDRAWALS
# =========================

class WithdrawalRequest(BaseModel):
    amount: float
    method: str  # "paypal", "crypto", etc.


class WithdrawalResponse(BaseModel):
    id: int
    user_id: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True