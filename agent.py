"""RAG 'Copilot' agent: hybrid-retrieve from Cosmos DB, then answer with the
Azure OpenAI Responses API, citing the retrieved agreements.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import config
import cosmos_store
from embeddings import embed_query

SYSTEM_PROMPT = (
    "You are a contract-intelligence assistant for a legal/operations team. "
    "Answer ONLY from the provided agreements context. Be concise and specific. "
    "Cite the agreements you use by their id and title, e.g. (agr-0001 — Master "
    "Services Agreement). If the context does not contain the answer, say so. "
    "When relevant, mention key facts like status, dates, contract value, "
    "renewal notice periods, and clause types."
)


@lru_cache(maxsize=1)
def _client():
    return config.make_openai_client(config.RESPONSES_API_VERSION)


def _context_block(results: list[dict[str, Any]]) -> str:
    blocks = []
    for r in results:
        clauses = "; ".join(
            f"{c['clauseType']}: {c['text']}" for c in r.get("clauses", [])
        )
        attrs = "; ".join(
            f"{a['name']}={a['value']}" for a in r.get("customAttributes", [])
        )
        blocks.append(
            f"[{r['id']}] {r['title']}\n"
            f"  type={r.get('type')} status={r.get('status')} "
            f"account={r.get('accountName')}\n"
            f"  created={r.get('createdDate')} updated={r.get('lastUpdated')} "
            f"expires={r.get('expirationDate')}\n"
            f"  summary: {r.get('content')}\n"
            f"  clauses: {clauses}\n"
            f"  attributes: {attrs}"
        )
    return "\n\n".join(blocks)


def answer(question: str, top_k: int = 6) -> dict[str, Any]:
    """Retrieve with hybrid search, then generate a grounded answer."""
    qvec = list(embed_query(question))
    retrieval = cosmos_store.search(
        capability="hybrid",
        query=question,
        top_k=top_k,
        query_vector=qvec,
    )
    results = retrieval["results"]
    context = _context_block(results)

    user_msg = (
        f"Question: {question}\n\n"
        f"Agreements context (top {len(results)} from Cosmos DB hybrid search):\n"
        f"{context}"
    )
    resp = _client().responses.create(
        model=config.CHAT_DEPLOYMENT,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    return {
        "answer": resp.output_text,
        "results": results,
        "sql": retrieval["sql"],
        "keywords": retrieval["keywords"],
    }
