# backend/src/app/db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()  # loads backend/.env

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://seatcheck:seatcheck@localhost:5432/seatcheck"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
