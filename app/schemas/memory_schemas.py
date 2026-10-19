from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LongTermMemoryCreate(BaseModel):
    memory_key: str = Field(min_length=1, max_length=100)
    memory_value: str = Field(min_length=1, max_length=2000)
    category: Literal[
        "fact",
        "preference",
        "goal",
        "decision",
        "correction",
    ] = "fact"
    source_conversation_id: str | None = None


class LongTermMemoryUpdate(BaseModel):
    memory_value: str = Field(min_length=1, max_length=2000)
    category: Literal[
        "fact",
        "preference",
        "goal",
        "decision",
        "correction",
    ] = "fact"


class LongTermMemoryResponse(BaseModel):
    id: str
    user_id: str
    memory_key: str
    memory_value: str
    category: str
    source_conversation_id: str | None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
