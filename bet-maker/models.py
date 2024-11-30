from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True)
    event_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    # noqa: E501


async def init_db(database_url: str):
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
