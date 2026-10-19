import re

from app import database

ALLOWED_CATEGORIES = {
    "fact",
    "preference",
    "goal",
    "decision",
    "correction",
}


def validate_memory(
    memory_key: str,
    memory_value: str,
    category: str,
) -> tuple[str, str, str]:
    key = memory_key.strip().lower()
    value = memory_value.strip()

    if not re.fullmatch(r"[a-z0-9_]+", key):
        raise ValueError(
            "Memory keys may contain only letters, numbers, and underscores."
        )

    if not value:
        raise ValueError("Memory value cannot be empty.")

    if category not in ALLOWED_CATEGORIES:
        raise ValueError("Invalid memory category.")

    return key, value, category


def create_memory(
    user_id: str,
    memory_key: str,
    memory_value: str,
    category: str,
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

    return database.save_long_term_memory(
        user_id=user_id,
        memory_key=key,
        memory_value=value,
        category=category,
        source_conversation_id=source_conversation_id,
    )


def get_memories(user_id: str) -> list[dict]:
    return database.list_long_term_memories(user_id)


def edit_memory(
    user_id: str,
    memory_id: str,
    memory_value: str,
    category: str,
) -> dict | None:
    _, value, category = validate_memory(
        "valid_key",
        memory_value,
        category,
    )

    return database.update_long_term_memory(
        user_id=user_id,
        memory_id=memory_id,
        memory_value=value,
        category=category,
    )


def remove_memory(user_id: str, memory_id: str) -> bool:
    return database.delete_long_term_memory(
        user_id=user_id,
        memory_id=memory_id,
    )


STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "i",
    "me",
    "my",
    "mine",
    "you",
    "your",
    "what",
    "when",
    "where",
    "which",
    "who",
    "how",
    "do",
    "does",
    "did",
    "can",
    "could",
    "would",
    "should",
    "to",
    "of",
    "in",
    "on",
    "for",
    "and",
    "or",
    "it",
    "this",
    "that",
    "with",
    "about",
    "tell",
    "please",
    "remember",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return {word for word in words if len(word) > 1 and word not in STOPWORDS}


def retrieve_relevant_memories(
    user_id: str,
    query: str,
    limit: int = 5,
) -> list[dict]:
    query_words = _tokenize(query)

    if not query_words:
        return []

    # Use the existing user-scoped database function.
    memories = database.list_long_term_memories(user_id)

    scored_memories = []

    for memory in memories:
        searchable_text = memory["memory_key"] + " " + memory["memory_value"]
        memory_words = _tokenize(searchable_text)

        overlap = query_words & memory_words

        if not overlap:
            continue

        score = len(overlap) / len(query_words)

        scored_memories.append((score, memory))

    scored_memories.sort(
        key=lambda item: (
            item[0],
            item[1]["updated_at"],
        ),
        reverse=True,
    )

    return [memory for score, memory in scored_memories[:limit]]
