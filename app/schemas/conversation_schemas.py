from datetime import datetime

from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
