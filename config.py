"""Central configuration for the Cosmos DB Search POC.

All connection details are read from environment variables (a local `.env` file is
loaded automatically). Nothing sensitive or environment-specific is hard-coded, so
the repository is safe to share publicly — copy `.env.example` to `.env` and fill in
your own resource names.

Auth: uses Azure AD (DefaultAzureCredential) by default, which works out of the box
when you are logged in via `az login`. Alternatively set AZURE_OPENAI_API_KEY and/or
COSMOS_KEY for key-based auth.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


def _require(name: str, value: str | None) -> str:
    if not value:
        raise ConfigError(
            f"Missing required setting '{name}'. Copy .env.example to .env and set it "
            f"(see README). Current value is empty."
        )
    return value


# ---- Azure OpenAI ----
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")  # optional; AAD used if unset

EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
EMBEDDING_API_VERSION = os.getenv("EMBEDDING_API_VERSION", "2024-10-21")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT", "gpt-4.1-mini")
RESPONSES_API_VERSION = os.getenv("RESPONSES_API_VERSION", "2025-04-01-preview")

# ---- Azure Cosmos DB for NoSQL (search backend) ----
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "docusign_demo")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "agreements")
COSMOS_KEY = os.getenv("COSMOS_KEY")  # optional; AAD used if unset

VECTOR_PATH = "/contentVector"
VECTOR_FIELD = "contentVector"

# ---- Search defaults ----
RRF_K = 60  # Reciprocal Rank Fusion constant (Cosmos DB default behaviour)


@lru_cache(maxsize=1)
def aad_token_provider():
    """Bearer token provider for Azure Cognitive Services (used when no API key)."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    return get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )


@lru_cache(maxsize=1)
def _azure_credential():
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def make_openai_client(api_version: str):
    """Create an AzureOpenAI client using key auth if available, else AAD."""
    from openai import AzureOpenAI

    endpoint = _require("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT)
    if AZURE_OPENAI_API_KEY:
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=api_version,
        )
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=aad_token_provider(),
        api_version=api_version,
    )


def make_cosmos_container():
    """Return the Cosmos DB container client (key auth if available, else AAD)."""
    from azure.cosmos import CosmosClient

    endpoint = _require("COSMOS_ENDPOINT", COSMOS_ENDPOINT)
    if COSMOS_KEY:
        client = CosmosClient(endpoint, credential=COSMOS_KEY)
    else:
        client = CosmosClient(endpoint, credential=_azure_credential())
    return client.get_database_client(COSMOS_DATABASE).get_container_client(
        COSMOS_CONTAINER
    )
