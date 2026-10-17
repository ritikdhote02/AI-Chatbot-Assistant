import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


@lru_cache(maxsize=1)
def get_chat_model() -> AzureChatOpenAI:
    required_variables = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ]
    missing = [name for name in required_variables if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0,
    )


def get_auth_settings() -> dict:
    import os

    secret = os.getenv("JWT_SECRET_KEY", "")

    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters.")

    return {
        "jwt_secret": secret,
        "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "access_token_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
        "app_base_url": os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
    }
