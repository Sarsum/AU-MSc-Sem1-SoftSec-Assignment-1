from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, relationship
from typing import List

# In-memory for now, can be easily changed to mysql for example
SQLALCHEMY_DATABASE_URL = 'sqlite:///db.sqlite'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DBBucket(Base):
    __tablename__ = "buckets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)

    transactions: Mapped[List["DBTransaction"]] = relationship(back_populates="bucket")

class DBTransaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bucket_id: Mapped[int] = mapped_column(ForeignKey("buckets.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    bucket: Mapped["DBBucket"] = relationship(back_populates="transactions")