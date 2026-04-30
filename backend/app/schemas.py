from typing import Optional
from pydantic import BaseModel, ConfigDict
from models import OrderStatus


class OrderCreate(BaseModel):
    item: str


class OrderUpdate(BaseModel):
    """Partial update schema for orders. Only provided fields are applied."""
    item: str | None = None
    status: OrderStatus | None = None


class OrderRead(BaseModel):
    id: int
    item: str
    status: OrderStatus

    model_config = ConfigDict(from_attributes=True)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class Message(BaseModel):
    role: str
    content: str
    timestamp: str