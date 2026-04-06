import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Security
    JWT_SECRET = os.getenv("JWT_SECRET")

    # Captcha
    HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET")

    # App Config
    APP_NAME = "dBaronX Affiliate Engine"

    # Subscription Tier Limits (Ads per day)
    TIERS = {
        "free": 5,
        "basic": 15,
        "pro": 40
    }

    # Revenue Split (Adjust later)
    REWARD_PERCENTAGE = 0.3  # 30% to user

    # System Limits
    MIN_WITHDRAWAL = 50.0
    MAX_DAILY_WITHDRAWAL = 1000.0

settings = Settings()