"""
Database configuration and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
)
# SessionLocal is kept as is for compatibility but documented as a constant
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()  # สร้าง Base Class สำหรับ Model


def get_db():
    """
    Dependency to get a database session.
    """
    db = SESSION_LOCAL()
    try:
        yield db  # ส่ง session ไปให้ API ทำงาน
    finally:
        db.close()  # ปิด session เมื่อ API ทำงานเสร็จ
