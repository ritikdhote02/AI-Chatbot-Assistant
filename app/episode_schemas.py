from datetime import datetime

from pydantic import BaseModel


class EpisodicMemoryResponse(BaseModel):
    id: str
    conversation_id: str
    title: str
    summary: str
    source_message_count: int
    created_at: datetime
    updated_at: datetime
