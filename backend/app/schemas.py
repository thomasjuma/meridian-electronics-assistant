from typing import List, Optional
from pydantic import BaseModel



# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    history: List[Message] = []