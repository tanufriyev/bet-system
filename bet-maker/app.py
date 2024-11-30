import os
from datetime import datetime
from typing import List

import httpx
from cache import RedisCache
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Bet, BetStatus, init_db
from schemas import BetRequest, BetResponse, EventResponse, EventUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(
    title="Bet Maker API",
    description="API for placing and managing bets on events",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LINE_PROVIDER_URL = os.getenv("LINE_PROVIDER_URL", "http://line-provider:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/betting")  # noqa: E501
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


async def get_session():
    if not hasattr(app.state, "session_factory"):
        app.state.session_factory = await init_db(DATABASE_URL)
    async with app.state.session_factory() as session:
        yield session


cache = RedisCache(REDIS_URL)


@app.get(
    "/events",
    response_model=List[EventResponse],
    summary="Get Available Events",
    description="Returns a list of events that are available for betting"
)
async def get_events():
    cached_events = await cache.get("events")
    if cached_events:
        return cached_events

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LINE_PROVIDER_URL}/events")
        if response.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail="Line provider service unavailable"
            )

        events = response.json()
        await cache.set("events", events, ttl=30)
        return events


@app.post("/bet", response_model=BetResponse)
async def place_bet(bet_request: BetRequest, session=Depends(get_session)):
    async with httpx.AsyncClient() as client:
        url = f"{LINE_PROVIDER_URL}/event/{bet_request.event_id}"
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Event not found")

        event = response.json()
        if datetime.fromtimestamp(event["deadline"]) < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="Event deadline has passed"
            )
        if event["state"] != "1":
            raise HTTPException(
                status_code=400,
                detail="Event already finished"
            )

    bet = Bet(
        event_id=bet_request.event_id,
        amount=bet_request.amount,
        status=BetStatus.PENDING
    )
    session.add(bet)
    await session.commit()

    return BetResponse.from_orm(bet)


@app.get("/bets", response_model=List[BetResponse])
async def get_bets(session=Depends(get_session)):
    result = await session.execute(select(Bet))
    bets = result.scalars().all()
    return [BetResponse.from_orm(bet) for bet in bets]


@app.post("/event-update")
async def event_update(
        event_data: EventUpdate,
        session: AsyncSession = Depends(get_session)
):
    query = select(Bet).where(Bet.event_id == event_data.event_id)
    result = await session.execute(query)
    bets = result.scalars().all()

    for bet in bets:
        if event_data.new_state == "FINISHED_WIN":
            bet.status = BetStatus.WON
        elif event_data.new_state == "FINISHED_LOSE":
            bet.status = BetStatus.LOST

    await session.commit()
    return {"status": "updated"}


@app.on_event("startup")
async def startup_event():
    app.state.cache = cache

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{LINE_PROVIDER_URL}/register-callback",
                json={"url": "http://bet-maker:8001"}
            )
        except Exception as e:
            print(f"Failed to register callback: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.cache.close()


@app.get("/internal/cache-stats")
async def cache_stats():
    info = await cache.get_info()
    return {
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "used_memory": info.get("used_memory_human", "unknown")
    }
