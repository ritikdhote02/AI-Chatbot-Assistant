import re
import uuid
from datetime import datetime, timezone

from app import database
from app.services import vector_store_service

ALLOWED_CATEGORIES = {
    "fact",
    "preference",
    "goal",
    "decision",
    "correction",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: str) -> str:
    value = ":".join(parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value))


def validate_memory(
    memory_key: str,
    memory_value: str,
    category: str,
) -> tuple[str, str, str]:
    key = memory_key.strip().lower()
    value = memory_value.strip()

    if not re.fullmatch(r"[a-z0-9_]+", key):
        raise ValueError(
            "Memory keys may contain only letters, numbers, " "and underscores."
        )

    if not value:
        raise ValueError("Memory value cannot be empty.")

    if len(key) > 100:
        raise ValueError("Memory key cannot exceed 100 characters.")

    if len(value) > 2000:
        raise ValueError("Memory value cannot exceed 2000 characters.")

    if category not in ALLOWED_CATEGORIES:
        raise ValueError("Invalid memory category.")

    return key, value, category


def _long_term_record(
    memory_id: str,
    metadata: dict,
    content: str,
) -> dict:
    return {
        "id": memory_id,
        "user_id": metadata["user_id"],
        "memory_key": metadata["memory_key"],
        "memory_value": metadata["memory_value"],
        "category": metadata["category"],
        "source_conversation_id": metadata.get("source_conversation_id"),
        "created_at": metadata["created_at"],
        "updated_at": metadata["updated_at"],
    }


def create_memory(
    user_id: str,
    memory_key: str,
    memory_value: str,
    category: str = "fact",
    source_conversation_id: str | None = None,
) -> dict:
    key, value, category = validate_memory(
        memory_key,
        memory_value,
        category,
    )

    if source_conversation_id is not None:
        conversation = database.get_conversation_for_user(
            source_conversation_id,
            user_id,
        )

        if conversation is None:
            raise ValueError("Source conversation not found.")

    memory_id = _stable_id(
        "long_term",
        user_id,
        key,
    )

    existing = vector_store_service.get_memory_by_id(memory_id)
    timestamp = _now()

    metadata = {
        "user_id": user_id,
        "memory_type": "long_term",
        "memory_key": key,
        "memory_value": value,
        "category": category,
        "created_at": (existing["metadata"]["created_at"] if existing else timestamp),
        "updated_at": timestamp,
    }

    if source_conversation_id is not None:
        metadata["source_conversation_id"] = source_conversation_id

    content = f"Memory key: {key}\n" f"Category: {category}\n" f"Fact: {value}"

    vector_store_service.upsert_memory(
        memory_id=memory_id,
        content=content,
        metadata=metadata,
    )

    return _long_term_record(
        memory_id,
        metadata,
        content,
    )


def get_memories(user_id: str) -> list[dict]:
    records = vector_store_service.list_memories(
        user_id=user_id,
        memory_type="long_term",
    )

    return [
        _long_term_record(
            record["id"],
            record["metadata"],
            record["content"],
        )
        for record in records
    ]


def edit_memory(
    user_id: str,
    memory_id: str,
    memory_value: str,
    category: str,
) -> dict | None:
    existing = vector_store_service.get_memory_by_id(memory_id)

    if (
        existing is None
        or existing["metadata"].get("user_id") != user_id
        or existing["metadata"].get("memory_type") != "long_term"
    ):
        return None

    key, value, category = validate_memory(
        existing["metadata"]["memory_key"],
        memory_value,
        category,
    )

    metadata = {
        **existing["metadata"],
        "memory_key": key,
        "memory_value": value,
        "category": category,
        "updated_at": _now(),
    }

    content = f"Memory key: {key}\n" f"Category: {category}\n" f"Fact: {value}"

    vector_store_service.upsert_memory(
        memory_id=memory_id,
        content=content,
        metadata=metadata,
    )

    return _long_term_record(
        memory_id,
        metadata,
        content,
    )


def remove_memory(
    user_id: str,
    memory_id: str,
) -> bool:
    existing = vector_store_service.get_memory_by_id(memory_id)

    if (
        existing is None
        or existing["metadata"].get("user_id") != user_id
        or existing["metadata"].get("memory_type") != "long_term"
    ):
        return False

    vector_store_service.delete_memory(memory_id)
    return True


def retrieve_relevant_memories(
    user_id: str,
    query: str,
    limit: int = 5,
) -> list[dict]:
    results = vector_store_service.search_memories(
        user_id=user_id,
        query=query,
        limit=limit,
        memory_type="long_term",
    )

    memories = []

    for result in results:
        metadata = result["metadata"]

        memories.append(
            {
                "id": result["id"],
                "user_id": metadata["user_id"],
                "memory_key": metadata["memory_key"],
                "memory_value": metadata["memory_value"],
                "category": metadata["category"],
                "source_conversation_id": metadata.get("source_conversation_id"),
                "distance": result["distance"],
            }
        )

    return memories


def save_episodic_memory(
    user_id: str,
    conversation_id: str,
    title: str,
    summary: str,
    source_message_count: int,
) -> dict:
    conversation = database.get_conversation_for_user(
        conversation_id,
        user_id,
    )

    if conversation is None:
        raise ValueError("Conversation not found.")

    if not summary.strip():
        raise ValueError("Episode summary cannot be empty.")

    episode_id = _stable_id(
        "episodic",
        user_id,
        conversation_id,
    )

    existing = vector_store_service.get_memory_by_id(episode_id)

    timestamp = _now()

    metadata = {
        "user_id": user_id,
        "memory_type": "episodic",
        "conversation_id": conversation_id,
        "title": title.strip() or "Conversation episode",
        "source_message_count": max(0, source_message_count),
        "created_at": (existing["metadata"]["created_at"] if existing else timestamp),
        "updated_at": timestamp,
    }

    content = (
        f"Episode title: {metadata['title']}\n"
        f"Conversation summary: {summary.strip()}"
    )

    vector_store_service.upsert_memory(
        memory_id=episode_id,
        content=content,
        metadata=metadata,
    )

    return {
        "id": episode_id,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "title": metadata["title"],
        "summary": summary.strip(),
        "source_message_count": metadata["source_message_count"],
        "created_at": metadata["created_at"],
        "updated_at": metadata["updated_at"],
    }


def list_episodic_memories(user_id: str) -> list[dict]:
    records = vector_store_service.list_memories(
        user_id=user_id,
        memory_type="episodic",
    )

    episodes = []

    for record in records:
        metadata = record["metadata"]
        content = record["content"]
        summary_prefix = "Conversation summary:"

        summary = (
            content.split(summary_prefix, 1)[1].strip()
            if summary_prefix in content
            else content
        )

        episodes.append(
            {
                "id": record["id"],
                "user_id": metadata["user_id"],
                "conversation_id": metadata["conversation_id"],
                "title": metadata["title"],
                "summary": summary,
                "source_message_count": metadata["source_message_count"],
                "created_at": metadata["created_at"],
                "updated_at": metadata["updated_at"],
            }
        )

    return episodes


def get_relevant_episodic_memories(
    user_id: str,
    query: str,
    limit: int = 3,
) -> list[dict]:
    results = vector_store_service.search_memories(
        user_id=user_id,
        query=query,
        limit=limit,
        memory_type="episodic",
    )

    episodes = []

    for result in results:
        metadata = result["metadata"]
        content = result["content"]
        summary_prefix = "Conversation summary:"

        summary = (
            content.split(summary_prefix, 1)[1].strip()
            if summary_prefix in content
            else content
        )

        episodes.append(
            {
                "id": result["id"],
                "user_id": metadata["user_id"],
                "conversation_id": metadata["conversation_id"],
                "title": metadata["title"],
                "summary": summary,
                "source_message_count": metadata["source_message_count"],
                "created_at": metadata["created_at"],
                "updated_at": metadata["updated_at"],
                "distance": result["distance"],
            }
        )

    return episodes
