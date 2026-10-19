import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.services.embedding_service import get_embedding_model

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    """Return the persistent ChromaDB vector store."""
    persist_directory = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        "data/chroma_db",
    )

    collection_name = os.getenv(
        "CHROMA_COLLECTION_NAME",
        "assistant_memories",
    )

    storage_path = Path(persist_directory)

    if not storage_path.is_absolute():
        storage_path = PROJECT_ROOT / storage_path

    storage_path.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embedding_model(),
        persist_directory=str(storage_path),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _build_filter(
    user_id: str,
    memory_type: str | None = None,
) -> dict:
    """
    Build a valid ChromaDB metadata filter.

    Every search is scoped to the authenticated user.
    When memory_type is provided, both conditions are combined
    using ChromaDB's $and operator.
    """
    conditions = [
        {"user_id": {"$eq": user_id}},
    ]

    if memory_type is not None:
        conditions.append({"memory_type": {"$eq": memory_type}})

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}


def upsert_memory(
    memory_id: str,
    content: str,
    metadata: dict,
) -> None:
    """Insert a memory or update the existing record with the same ID."""
    document = Document(
        id=memory_id,
        page_content=content,
        metadata=metadata,
    )

    get_vector_store().add_documents(
        documents=[document],
        ids=[memory_id],
    )


def get_memory_by_id(memory_id: str) -> dict | None:
    """Retrieve one memory by its ChromaDB ID."""
    result = get_vector_store().get(
        ids=[memory_id],
        include=["documents", "metadatas"],
    )

    if not result["ids"]:
        return None

    return {
        "id": result["ids"][0],
        "content": result["documents"][0],
        "metadata": result["metadatas"][0],
    }


def list_memories(
    user_id: str,
    memory_type: str | None = None,
) -> list[dict]:
    """List memories belonging to one user, optionally by type."""
    filters = _build_filter(
        user_id=user_id,
        memory_type=memory_type,
    )

    result = get_vector_store().get(
        where=filters,
        include=["documents", "metadatas"],
    )

    memories = []

    for index, memory_id in enumerate(result["ids"]):
        memories.append(
            {
                "id": memory_id,
                "content": result["documents"][index],
                "metadata": result["metadatas"][index],
            }
        )

    return memories


def search_memories(
    user_id: str,
    query: str,
    limit: int = 5,
    memory_type: str | None = None,
) -> list[dict]:
    """Search a user's memories by semantic similarity."""
    if not query.strip() or limit <= 0:
        return []

    filters = _build_filter(
        user_id=user_id,
        memory_type=memory_type,
    )

    results = get_vector_store().similarity_search_with_score(
        query=query,
        k=limit,
        filter=filters,
    )

    return [
        {
            "id": document.id,
            "content": document.page_content,
            "metadata": document.metadata,
            "distance": distance,
        }
        for document, distance in results
    ]


def delete_memory(memory_id: str) -> None:
    """Delete a memory by its ChromaDB ID."""
    get_vector_store().delete(ids=[memory_id])
