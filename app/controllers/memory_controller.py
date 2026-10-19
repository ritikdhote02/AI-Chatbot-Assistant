import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_conversation_for_user
from app.schemas.episode_schemas import EpisodicMemoryResponse
from app.schemas.memory_schemas import (
    LongTermMemoryCreate,
    LongTermMemoryResponse,
    LongTermMemoryUpdate,
)
from app.security import get_current_user
from app.services import memory_service
from app.services.episode_service import summarize_conversation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/conversations/{conversation_id}/episode",
    response_model=EpisodicMemoryResponse,
    tags=["Episodic Memory"],
)
def create_or_refresh_episode(
    conversation_id: str,
    current_user=Depends(get_current_user),
):
    # Verify ownership before reading or summarizing the conversation.
    conversation = get_conversation_for_user(
        conversation_id,
        current_user["id"],
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    try:
        return summarize_conversation(
            user_id=current_user["id"],
            conversation=dict(conversation),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Episode summarization failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not summarize the conversation.",
        ) from exc


@router.get(
    "/episodes",
    response_model=list[EpisodicMemoryResponse],
    tags=["Episodic Memory"],
)
def get_my_episodes(
    current_user=Depends(get_current_user),
):
    return memory_service.list_episodic_memories(current_user["id"])


@router.post(
    "/memories",
    response_model=LongTermMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Long Term Memory"],
)
def create_long_term_memory(
    request: LongTermMemoryCreate,
    current_user=Depends(get_current_user),
):
    try:
        return memory_service.create_memory(
            user_id=current_user["id"],
            memory_key=request.memory_key,
            memory_value=request.memory_value,
            category=request.category,
            source_conversation_id=request.source_conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/memories",
    response_model=list[LongTermMemoryResponse],
    tags=["Long Term Memory"],
)
def list_long_term_memories(
    current_user=Depends(get_current_user),
):
    return memory_service.get_memories(current_user["id"])


@router.patch(
    "/memories/{memory_id}",
    response_model=LongTermMemoryResponse,
    tags=["Long Term Memory"],
)
def update_long_term_memory(
    memory_id: str,
    request: LongTermMemoryUpdate,
    current_user=Depends(get_current_user),
):
    result = memory_service.edit_memory(
        user_id=current_user["id"],
        memory_id=memory_id,
        memory_value=request.memory_value,
        category=request.category,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )

    return result


@router.delete(
    "/memories/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Long Term Memory"],
)
def delete_long_term_memory(
    memory_id: str,
    current_user=Depends(get_current_user),
):
    deleted = memory_service.remove_memory(
        user_id=current_user["id"],
        memory_id=memory_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )

    return None
