"""Embed the Docusign-domain agreements and upsert them into Cosmos DB.

Merges the curated agreements (`data_gen.py`) with any LLM-generated agreements
(`data/generated_agreements.json`, produced by `generate_data.py`), embeds each one
with Azure OpenAI, and upserts into the Cosmos DB container.

Usage:  python build_index.py
Re-run any time; upserts are idempotent on `id`.
"""
from __future__ import annotations

import json
import os
import sys
import time

import config
from data_gen import AGREEMENTS, embedding_text
from embeddings import embed_texts

GENERATED_PATH = os.path.join(os.path.dirname(__file__), "data", "generated_agreements.json")


def load_corpus() -> list[dict]:
    docs = list(AGREEMENTS)
    if os.path.exists(GENERATED_PATH):
        with open(GENERATED_PATH) as f:
            extra = json.load(f)
        seen = {d["id"] for d in docs}
        added = [d for d in extra if d["id"] not in seen]
        docs.extend(added)
        print(f"Merged {len(added)} LLM-generated agreements from "
              f"{os.path.basename(GENERATED_PATH)}")
    return docs


def main() -> int:
    container = config.make_cosmos_container()
    docs = load_corpus()
    print(f"Embedding {len(docs)} agreements with '{config.EMBEDDING_DEPLOYMENT}' and "
          f"upserting to {config.COSMOS_DATABASE}/{config.COSMOS_CONTAINER} …")

    texts = [embedding_text(d) for d in docs]
    t0 = time.time()
    vectors: list[list[float]] = []
    BATCH = 16
    for i in range(0, len(texts), BATCH):
        vectors.extend(embed_texts(texts[i : i + BATCH]))
        print(f"  embedded {min(i + BATCH, len(texts))}/{len(texts)}")
    print(f"Embedding done in {time.time() - t0:.1f}s")

    for doc, vec in zip(docs, vectors):
        item = dict(doc)
        item[config.VECTOR_FIELD] = vec
        container.upsert_item(item)
    print(f"Upserted {len(docs)} documents.")

    count = list(container.query_items(
        query="SELECT VALUE COUNT(1) FROM c",
        enable_cross_partition_query=True,
    ))[0]
    print(f"Container now holds {count} documents. Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
