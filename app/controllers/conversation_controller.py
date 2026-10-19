import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.database import (
    create_conversation,
    get_conversation_for_user,
    get_conversation_messages,
    get_user_message_count,
    list_conversations,
)
from app.schemas.conversation_schemas import (
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.schemas.memory_extraction_schemas import MemoryExtractionRunResponse
from app.security import get_current_user
from app.services.chat_service import run_conversation_chat
from app.services.memory_extraction_service import extract_and_save_memories

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Communication"],
)
def create_new_conversation(
    current_user=Depends(get_current_user),
):
    return create_conversation(current_user["id"])


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    tags=["Communication"],
)
def get_my_conversations(
    current_user=Depends(get_current_user),
):
    return list_conversations(current_user["id"])


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
    tags=["Communication"],
)
def get_messages(
    conversation_id: str,
    current_user=Depends(get_current_user),
):
    conversation = get_conversation_for_user(
        conversation_id,
        current_user["id"],
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return get_conversation_messages(conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
    tags=["Communication"],
)
def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    # Verify ownership before reading history or calling the LLM.
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
        answer = run_conversation_chat(
            user_id=current_user["id"],
            conversation_id=conversation_id,
            user_message=request.message,
        )
    except Exception as exc:
        logger.exception("Conversation request failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The chat request failed. Check the server logs.",
        ) from exc

    # Schedule extraction after every five user messages.
    # run_conversation_chat saves the exchange before returning.
    try:
        user_message_count = get_user_message_count(conversation_id)

        if user_message_count > 0 and user_message_count % 5 == 0:
            background_tasks.add_task(
                run_background_memory_extraction,
                current_user["id"],
                conversation_id,
            )
    except Exception:
        # Do not fail a successful chat because scheduling failed.
        logger.exception(
            "Could not schedule memory extraction: conversation_id=%s",
            conversation_id,
        )

    return ChatResponse(
        conversation_id=conversation_id,
        answer=answer,
    )


@router.post(
    "/conversations/{conversation_id}/extract-memories",
    response_model=MemoryExtractionRunResponse,
    tags=["Memory Extraction"],
)
def extract_conversation_memories(
    conversation_id: str,
    current_user=Depends(get_current_user),
):
    # Confirm that this conversation belongs to the logged-in user.
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
        result = extract_and_save_memories(
            user_id=current_user["id"],
            conversation_id=conversation_id,
        )
        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Memory extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not extract memories from the conversation.",
        ) from exc


def run_background_memory_extraction(
    user_id: str,
    conversation_id: str,
) -> None:
    """Extract and save memories without failing the chat request."""
    try:
        result = extract_and_save_memories(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        logger.info(
            "Background memory extraction completed: "
            "conversation_id=%s candidates=%s saved=%s",
            conversation_id,
            result["candidates_found"],
            result["saved_count"],
        )

    except Exception:
        logger.exception(
            "Background memory extraction failed: conversation_id=%s",
            conversation_id,
        )
