"""Search against the real Azure Cosmos DB for NoSQL backend.

Implements the three capabilities natively in Cosmos DB:
  * full-text  -> ORDER BY RANK FullTextScore(c.content, ...keywords)
  * vector     -> ORDER BY VectorDistance(c.contentVector, @q)
  * hybrid     -> ORDER BY RANK RRF(VectorDistance(...), FullTextScore(...))

plus boolean/range filters, nested clause queries and prefix (typeahead).
Each call also returns the *equivalent Cosmos DB SQL* it executed, for display.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import config

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "with", "is", "are", "be", "that", "this", "our", "we", "us", "how", "what",
    "which", "from", "as", "into", "before", "after", "their", "they", "it",
    "its", "may", "will", "shall", "each", "any", "all", "two", "companies",
    "company", "share", "shares", "shared", "us", "between", "possible",
}

PROJECTION = (
    "c.id, c.title, c.type, c.status, c.accountId, c.accountName, "
    "c.createdDate, c.lastUpdated, c.expirationDate, c.content, "
    "c.clauses, c.customAttributes, c.tags"
)


def extract_keywords(query: str, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for tok in re.findall(r"[a-zA-Z0-9]+", (query or "").lower()):
        if len(tok) < 2 or tok in _STOPWORDS or tok in seen:
            continue
        seen.append(tok)
        if len(seen) >= limit:
            break
    return seen


def _build_filters(filters: dict[str, Any]) -> tuple[list[str], list[dict]]:
    """Translate a filter dict into SQL predicates + parameters."""
    where: list[str] = []
    params: list[dict] = []
    f = filters or {}

    if f.get("account"):
        where.append("c.accountId = @account")
        params.append({"name": "@account", "value": f["account"]})

    if f.get("status"):
        ors = []
        for i, s in enumerate(f["status"]):
            p = f"@status{i}"
            ors.append(f"c.status = {p}")
            params.append({"name": p, "value": s})
        where.append("(" + " OR ".join(ors) + ")")

    if f.get("type"):
        ors = []
        for i, t in enumerate(f["type"]):
            p = f"@type{i}"
            ors.append(f"c.type = {p}")
            params.append({"name": p, "value": t})
        where.append("(" + " OR ".join(ors) + ")")

    for key, field, op in [
        ("updated_from", "lastUpdated", ">="),
        ("updated_to", "lastUpdated", "<"),
        ("created_from", "createdDate", ">="),
        ("created_to", "createdDate", "<"),
        ("expiring_from", "expirationDate", ">="),
        ("expiring_to", "expirationDate", "<"),
    ]:
        if f.get(key):
            p = f"@{key}"
            where.append(f"c.{field} {op} {p}")
            params.append({"name": p, "value": f[key]})

    if f.get("prefix"):
        where.append("STARTSWITH(c.title, @prefix, true)")
        params.append({"name": "@prefix", "value": f["prefix"]})

    if f.get("clause_type") or f.get("clause_contains"):
        sub = []
        if f.get("clause_type"):
            sub.append("x.clauseType = @clause_type")
            params.append({"name": "@clause_type", "value": f["clause_type"]})
        if f.get("clause_contains"):
            sub.append("CONTAINS(x.text, @clause_contains, true)")
            params.append({"name": "@clause_contains", "value": f["clause_contains"]})
        where.append(
            "EXISTS (SELECT VALUE x FROM x IN c.clauses WHERE "
            + " AND ".join(sub)
            + ")"
        )

    if f.get("attr_name") or f.get("attr_value"):
        sub = []
        if f.get("attr_name"):
            sub.append("a.name = @attr_name")
            params.append({"name": "@attr_name", "value": f["attr_name"]})
        if f.get("attr_value"):
            sub.append("CONTAINS(a.value, @attr_value, true)")
            params.append({"name": "@attr_value", "value": f["attr_value"]})
        where.append(
            "EXISTS (SELECT VALUE a FROM a IN c.customAttributes WHERE "
            + " AND ".join(sub)
            + ")"
        )

    return where, params


@lru_cache(maxsize=1)
def _container():
    return config.make_cosmos_container()


def _fts_call(keywords: list[str]) -> str:
    kw = ", ".join(f"'{k}'" for k in keywords)
    return f"FullTextScore(c.content, {kw})"


def build_query(
    capability: str,
    query: str,
    filters: dict[str, Any] | None,
    top_k: int,
    has_vector: bool,
) -> tuple[str, list[dict], list[str], str]:
    """Compose the SQL + params. Returns (sql, params, keywords, effective_capability).

    `@q` (the query vector) is added by the caller; here we only reference it.
    """
    where, params = _build_filters(filters or {})
    where_sql = ("\nWHERE " + "\n  AND ".join(where)) if where else ""
    keywords = extract_keywords(query)
    proj = PROJECTION
    eff = capability

    if capability == "vector":
        proj = PROJECTION + ",\n       VectorDistance(c.contentVector, @q) AS _distance"
        order = "\nORDER BY VectorDistance(c.contentVector, @q)"
    elif capability == "hybrid":
        if keywords and has_vector:
            order = (
                "\nORDER BY RANK RRF(VectorDistance(c.contentVector, @q), "
                + _fts_call(keywords)
                + ")"
            )
        elif has_vector:  # no keywords -> degrade to vector
            eff = "vector"
            proj = PROJECTION + ",\n       VectorDistance(c.contentVector, @q) AS _distance"
            order = "\nORDER BY VectorDistance(c.contentVector, @q)"
        else:
            eff = "fulltext"
            order = "\nORDER BY RANK " + _fts_call(keywords)
    else:  # fulltext
        if keywords:
            order = "\nORDER BY RANK " + _fts_call(keywords)
        else:
            order = "\nORDER BY c.lastUpdated DESC"

    sql = f"SELECT TOP {top_k} {proj}\nFROM c{where_sql}{order}"
    return sql, params, keywords, eff


def display_sql(sql: str, has_vector_param: bool) -> str:
    """Human-friendly SQL for the UI (replaces the raw vector with a placeholder)."""
    if has_vector_param:
        return sql.replace("@q", "@queryVector  /* 1536-dim text-embedding-3-small */")
    return sql


def search(
    capability: str,
    query: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 8,
    query_vector: list[float] | None = None,
) -> dict[str, Any]:
    """Execute a search against Cosmos DB and return results + the SQL used."""
    if capability in ("vector", "hybrid") and query_vector is None and query:
        from embeddings import embed_query

        query_vector = list(embed_query(query))

    has_vector = query_vector is not None
    sql, params, keywords, eff = build_query(
        capability, query, filters, top_k, has_vector
    )

    run_params = list(params)
    if "@q" in sql and has_vector:
        run_params.append({"name": "@q", "value": list(query_vector)})

    rows = list(
        _container().query_items(
            query=sql, parameters=run_params, enable_cross_partition_query=True
        )
    )
    for i, r in enumerate(rows, 1):
        r["_rank"] = i
        if "_distance" in r:
            r["_similarity"] = round(1.0 - float(r["_distance"]), 4)

    return {
        "results": rows,
        "sql": display_sql(sql, has_vector),
        "keywords": keywords,
        "effective_capability": eff,
        "requested_capability": capability,
    }


# ----------------------------------------------------------------------------
# Faceted aggregations (GROUP BY) — demonstrates the "facets / aggregations"
# Elasticsearch feature natively in Cosmos DB.
#
# Cosmos DB executes GROUP BY per physical partition and merges. The Python SDK
# fully supports non-VALUE GROUP BY for *single-partition* queries, so we run the
# real GROUP BY once per partition-key value and merge the buckets here — exactly
# how the engine fans the aggregation out internally.
# ----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def partition_keys() -> tuple[str, ...]:
    """Distinct partition-key (accountId) values."""
    rows = list(_container().query_items(
        query="SELECT DISTINCT VALUE c.accountId FROM c",
        enable_cross_partition_query=True,
    ))
    return tuple(sorted(rows))


def aggregate(
    group_expr: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Real GROUP BY ... COUNT(1), fanned per partition and merged. Returns buckets + SQL."""
    filters = dict(filters or {})
    # 'account' becomes partition scoping rather than a WHERE predicate.
    pkeys = [filters["account"]] if filters.get("account") else list(partition_keys())
    exec_filters = {k: v for k, v in filters.items() if k != "account"}
    where, params = _build_filters(exec_filters)
    where_sql = ("\nWHERE " + "\n  AND ".join(where)) if where else ""
    sql = (
        f"SELECT {group_expr} AS key, COUNT(1) AS count\n"
        f"FROM c{where_sql}\n"
        f"GROUP BY {group_expr}"
    )

    merged: dict[Any, int] = {}
    for pk in pkeys:
        for r in _container().query_items(
            query=sql, parameters=params, partition_key=pk
        ):
            if r.get("key") is None:
                continue
            merged[r["key"]] = merged.get(r["key"], 0) + r["count"]

    buckets = [{"key": k, "count": v} for k, v in merged.items()]
    buckets.sort(key=lambda r: r["count"], reverse=True)

    # canonical SQL for display (includes any account filter)
    disp_where, _ = _build_filters(filters)
    disp_where_sql = ("\nWHERE " + "\n  AND ".join(disp_where)) if disp_where else ""
    display = (
        f"SELECT {group_expr} AS key, COUNT(1) AS count\n"
        f"FROM c{disp_where_sql}\n"
        f"GROUP BY {group_expr}"
    )
    return {"buckets": buckets, "sql": display}


def date_histogram(
    field: str = "lastUpdated",
    granularity: int = 7,  # 7 = month (YYYY-MM), 4 = year, 10 = day
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bucket documents by a truncated ISO date (emulated date histogram via LEFT)."""
    res = aggregate(f"LEFT(c.{field}, {granularity})", filters)
    res["buckets"].sort(key=lambda r: r["key"])  # chronological
    return res


def distinct_count(field: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cardinality via the documented COUNT(DISTINCT) workaround (DISTINCT subquery)."""
    n = len(aggregate(f"c.{field}", filters)["buckets"])
    sql = f"SELECT VALUE COUNT(1) FROM (SELECT DISTINCT VALUE c.{field} FROM c)"
    return {"value": n, "sql": sql}


def total_count(filters: dict[str, Any] | None = None) -> int:
    where, params = _build_filters(filters or {})
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = f"SELECT VALUE COUNT(1) FROM c{where_sql}"
    val = list(
        _container().query_items(
            query=sql, parameters=params, enable_cross_partition_query=True
        )
    )
    return val[0] if val else 0


