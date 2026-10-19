import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()


@lru_cache(maxsize=1)
def get_embedding_model() -> AzureOpenAIEmbeddings:
    deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME": deployment_name,
            "AZURE_OPENAI_ENDPOINT": endpoint,
            "AZURE_OPENAI_API_KEY": api_key,
            "AZURE_OPENAI_API_VERSION": api_version,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError("Missing embedding configuration: " + ", ".join(missing))

    return AzureOpenAIEmbeddings(
        azure_deployment=deployment_name,
        azure_endpoint=endpoint,
        api_key=api_key,
        openai_api_version=api_version,
    )


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.embed_query(text)
