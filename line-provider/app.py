import decimal
import enum
import time
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class EventState(str, enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


events: dict[str, Event] = {
    '1': Event(event_id='1', coefficient=1.2, deadline=int(time.time()) + 600, state=EventState.NEW),
    '2': Event(event_id='2', coefficient=1.15, deadline=int(time.time()) + 60, state=EventState.NEW),
    '3': Event(event_id='3', coefficient=1.67, deadline=int(time.time()) + 90, state=EventState.NEW)
}

app = FastAPI()


@app.put('/event')
async def create_event(event: Event):
    if event.event_id not in events:
        events[event.event_id] = event
        return {}

    for p_name, p_value in event.dict(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)

    return {}


@app.get('/event/{event_id}')
async def get_event(event_id: str):
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@app.get('/events')
async def get_events():
    return list(e for e in events.values() if time.time() < e.deadline)


callback_urls: List[str] = []


class CallbackRequestBody(BaseModel):
    url: str


@app.post("/register-callback")
async def register_callback(callback_url: CallbackRequestBody):
    if callback_url.url not in callback_urls:
        callback_urls.append(callback_url.url)
    return {"status": "registered"}


async def notify_status_change(event_id: str, new_state: EventState):
    """Notify all registered services about event status change"""
    for callback_url in callback_urls:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{callback_url}/event-update",
                    json={
                        "event_id": event_id,
                        "new_state": new_state.name
                    }
                )
        except Exception as e:
            print(f"Failed to notify {callback_url}: {e}")


class StateUpdate(BaseModel):
    state: EventState


@app.post("/change-event-state/{event_id}")
async def change_event_state(event_id: str, new_state: StateUpdate):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Event not found")

    event = events[event_id]
    event.state = new_state.state
    events[event_id] = event

    await notify_status_change(event_id, new_state.state)

    return event
