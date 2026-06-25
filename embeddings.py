"""Azure OpenAI embeddings (text-embedding-3-small) via AAD or API key."""
from __future__ import annotations

from functools import lru_cache

import config


@lru_cache(maxsize=1)
def _client():
    return config.make_openai_client(config.EMBEDDING_API_VERSION)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts; returns one vector per input."""
    if not texts:
        return []
    resp = _client().embeddings.create(
        model=config.EMBEDDING_DEPLOYMENT, input=texts
    )
    # API preserves input order.
    return [d.embedding for d in resp.data]


@lru_cache(maxsize=512)
def embed_query(text: str) -> tuple[float, ...]:
    """Embed a single query string (cached). Returns a tuple so it is hashable."""
    return tuple(embed_texts([text])[0])
