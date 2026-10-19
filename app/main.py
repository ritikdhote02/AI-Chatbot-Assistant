import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.controllers import (
    auth_controller,
    conversation_controller,
    memory_controller,
)
from app.database import init_db

logging.basicConfig(level=logging.INFO)


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

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


app.include_router(auth_controller.router)
app.include_router(conversation_controller.router)
app.include_router(memory_controller.router)
