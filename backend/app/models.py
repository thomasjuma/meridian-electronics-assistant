from sqlalchemy import Column, Integer, String, Enum
from database import Base
import enum
from pydantic import BaseModel
from typing import Optional


class OrderStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    FULFILLED = "fulfilled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.RECEIVED)

# ChatRequest/Response models
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
