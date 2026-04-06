import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL notset in .env or Render env vars")
    
engine = create_engine(
   DATABASE_URL,
   pool_pre_ping=True,
   pool_size=10,
   max_overflow=20,
   echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SssionLocal()
    try:
        yield db
    finally:
        db.close()