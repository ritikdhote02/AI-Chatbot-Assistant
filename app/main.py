import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from app.config import get_auth_settings
from app.database import (
    create_conversation,
    get_conversation_for_user,
    get_conversation_messages,
    get_user_message_count,
    init_db,
    list_conversations,
)
from app.schemas.auth_schemas import (
    AuthTokenResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    UserResponse,
)
from app.schemas.conversation_schemas import ChatResponse as ConversationChatResponse
from app.schemas.conversation_schemas import (
    ConversationResponse,
)
from app.schemas.conversation_schemas import (
    MessageResponse as ConversationMessageResponse,
)
from app.schemas.conversation_schemas import (
    SendMessageRequest,
)
from app.schemas.episode_schemas import EpisodicMemoryResponse
from app.schemas.memory_extraction_schemas import MemoryExtractionRunResponse
from app.schemas.memory_schemas import (
    LongTermMemoryCreate,
    LongTermMemoryResponse,
    LongTermMemoryUpdate,
)
from app.security import get_current_user
from app.services import memory_service
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_verification_token,
    get_user_by_email,
    register_user,
    verify_email_token,
)
from app.services.chat_service import run_conversation_chat
from app.services.email_service import send_verification_email
from app.services.episode_service import summarize_conversation
from app.services.memory_extraction_service import extract_and_save_memories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables for authentication and conversations.
    init_db()
    yield


app = FastAPI(
    title="AI Knowledge Assistant",
    description=(
        "Authenticated AI assistant with conversation history "
        "and semantic memory powered by ChromaDB."
    ),
    version="0.3.0",
    lifespan=lifespan,
)


def send_verification_link(email: str, token: str) -> None:
    settings = get_auth_settings()
    verification_url = (
        f"{settings['app_base_url']}/auth/verify-email"
        f"?token={quote(token, safe='')}"
    )
    send_verification_email(email, verification_url)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------


@app.post(
    "/auth/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(request: RegisterRequest):
    try:
        _, token = register_user(
            name=request.name,
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    try:
        send_verification_link(str(request.email), token)
    except Exception as exc:
        logger.exception("Could not send verification email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Your account was created but the verification email "
                "could not be sent. Please try the resend endpoint."
            ),
        ) from exc

    return MessageResponse(
        message="Account created. Check your email to verify your address."
    )


@app.get(
    "/auth/verify-email",
    response_class=HTMLResponse,
    tags=["Authentication"],
)
def verify_email(token: str):
    if not token or len(token) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link.",
        )

    if not verify_email_token(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification link is invalid or has expired.",
        )

    return HTMLResponse("""
        <!doctype html>
        <html>
          <head><title>Email verified</title></head>
          <body>
            <h1>Email verified successfully!</h1>
            <p>You can now return to the application and log in.</p>
          </body>
        </html>
        """)


@app.post(
    "/auth/resend-verification",
    response_model=MessageResponse,
    tags=["Authentication"],
)
def resend_verification(request: ResendVerificationRequest):
    user = get_user_by_email(str(request.email))

    # Avoid revealing whether an email belongs to an account.
    if user is None or user["is_email_verified"]:
        return MessageResponse(
            message=(
                "If an unverified account exists for this email, "
                "a verification email will be sent."
            )
        )

    token = create_verification_token(user["id"])

    try:
        send_verification_link(user["email"], token)
    except Exception as exc:
        logger.exception("Could not resend verification email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The verification email could not be sent. Try again later.",
        ) from exc

    return MessageResponse(
        message=(
            "If an unverified account exists for this email, "
            "a verification email will be sent."
        )
    )


@app.post(
    "/auth/login",
    response_model=AuthTokenResponse,
    tags=["Authentication"],
)
def login(request: LoginRequest):
    user, error = authenticate_user(
        email=str(request.email),
        password=request.password,
    )

    if error == "email_not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in.",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(user["id"])

    return AuthTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@app.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["Authentication"],
)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        is_email_verified=bool(current_user["is_email_verified"]),
    )


# ---------------------------------------------------------------------
# Conversations and messages (SQLite)
# ---------------------------------------------------------------------


@app.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Communication"],
)
def create_new_conversation(
    current_user=Depends(get_current_user),
):
    return create_conversation(current_user["id"])


@app.get(
    "/conversations",
    response_model=list[ConversationResponse],
    tags=["Communication"],
)
def get_my_conversations(
    current_user=Depends(get_current_user),
):
    return list_conversations(current_user["id"])


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ConversationMessageResponse],
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


@app.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationChatResponse,
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

    return ConversationChatResponse(
        conversation_id=conversation_id,
        answer=answer,
    )


# ---------------------------------------------------------------------
# Episodic memory (ChromaDB)
# ---------------------------------------------------------------------


@app.post(
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


@app.get(
    "/episodes",
    response_model=list[EpisodicMemoryResponse],
    tags=["Episodic Memory"],
)
def get_my_episodes(
    current_user=Depends(get_current_user),
):
    return memory_service.list_episodic_memories(current_user["id"])


# ---------------------------------------------------------------------
# Long-term memory (ChromaDB)
# ---------------------------------------------------------------------


@app.post(
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


@app.get(
    "/memories",
    response_model=list[LongTermMemoryResponse],
    tags=["Long Term Memory"],
)
def list_long_term_memories(
    current_user=Depends(get_current_user),
):
    return memory_service.get_memories(current_user["id"])


@app.patch(
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


@app.delete(
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


@app.post(
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


# Background task to extract and save memories from a conversation
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
