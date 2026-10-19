from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.memory_schemas import LongTermMemoryResponse

MAX_MESSAGES = 30
MAX_MESSAGE_CHARS = 3000
MAX_TRANSCRIPT_CHARS = 20000
MAX_CANDIDATES = 10

MemoryCategory = Literal[
    "fact",
    "preference",
    "goal",
    "decision",
    "correction",
]


class MemoryCandidate(BaseModel):
    """One potential long-term memory extracted from a conversation."""

    memory_key: str = Field(
        description=(
            "A concise, stable snake_case identifier, such as "
            "'career_goal' or 'preferred_programming_language'."
        ),
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$",
    )
    memory_value: str = Field(
        description=(
            "A concise statement explicitly supported by the user's "
            "conversation messages. Do not infer missing details."
        ),
        min_length=1,
        max_length=2000,
    )
    category: MemoryCategory = Field(
        description=(
            "The kind of memory: fact, preference, goal, decision, " "or correction."
        )
    )


class MemoryExtractionResult(BaseModel):
    """Structured result returned by the LLM."""

    memories: list[MemoryCandidate] = Field(
        default_factory=list,
        max_length=MAX_CANDIDATES,
        description=(
            "Only durable, useful, explicitly supported memories. "
            "Return an empty list when there are none."
        ),
    )


class MemoryExtractionRunResponse(BaseModel):
    conversation_id: str
    candidates_found: int
    saved_count: int
    memories: list[LongTermMemoryResponse] = Field(default_factory=list)
