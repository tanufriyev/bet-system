from datetime import datetime

from models import BetStatus
from pydantic import BaseModel, Field, field_serializer


class EventResponse(BaseModel):
    event_id: str
    coefficient: float
    deadline: int
    state: int

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "event1",
                "coefficient": 1.5,
                "deadline": 1732983614,
                "state": 1
            }
        }


class BetRequest(BaseModel):
    event_id: str
    amount: float = Field(..., gt=0)


class BetResponse(BaseModel):
    id: int
    event_id: str
    amount: float
    status: BetStatus
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime) -> str:
        return dt.isoformat()


class EventUpdate(BaseModel):
    event_id: str
    new_state: str
