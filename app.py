"""Streamlit UI for the Azure Cosmos DB search POC (Docusign domain).

Run:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re

import pandas as pd
import streamlit as st

import cosmos_store
from data_gen import ACCOUNTS, AGREEMENTS, AGENT_SUGGESTIONS, PREDEFINED_QUERIES

st.set_page_config(
    page_title="Cosmos DB Search · Docusign POC",
    page_icon="🔎",
    layout="wide",
)

STATUSES = sorted({d["status"] for d in AGREEMENTS})
TYPES = sorted({d["type"] for d in AGREEMENTS})
CLAUSE_TYPES = sorted({c["clauseType"] for d in AGREEMENTS for c in d["clauses"]})
ACCOUNT_OPTS = ["(any)"] + list(ACCOUNTS.keys())

CAP_LABELS = {
    "fulltext": "Full-text · BM25",
    "vector": "Vector · semantic",
    "hybrid": "Hybrid · RRF",
}
LABEL_TO_CAP = {v: k for k, v in CAP_LABELS.items()}
CAP_ORDER = ["fulltext", "vector", "hybrid"]

STATUS_COLORS = {
    "completed": "#1a7f37", "sent": "#0a7bbd", "delivered": "#7048e8",
    "declined": "#b35900", "voided": "#b21e2c",
}


# ----------------------------------------------------------------------------
# cached helpers
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=300)
def cached_count() -> int:
    c = cosmos_store._container()
    return list(c.query_items(query="SELECT VALUE COUNT(1) FROM c",
                              enable_cross_partition_query=True))[0]


@st.cache_data(show_spinner=False, ttl=300)
def cached_search(capability: str, query: str, filters_json: str, top_k: int) -> dict:
    filters = json.loads(filters_json)
    return cosmos_store.search(capability, query, filters, top_k=top_k)


@st.cache_data(show_spinner=False, ttl=300)
def cached_aggregate(group_expr: str, filters_json: str) -> dict:
    return cosmos_store.aggregate(group_expr, json.loads(filters_json))


@st.cache_data(show_spinner=False, ttl=300)
def cached_histogram(field: str, granularity: int, filters_json: str) -> dict:
    return cosmos_store.date_histogram(field, granularity, json.loads(filters_json))


@st.cache_data(show_spinner=False, ttl=300)
def cached_distinct(field: str) -> dict:
    return cosmos_store.distinct_count(field)


@st.cache_data(show_spinner=False, ttl=300)
def cached_total(filters_json: str) -> int:
    return cosmos_store.total_count(json.loads(filters_json))


def highlight(text: str, keywords: list[str], max_len: int = 320) -> str:
    """Return an HTML snippet with keyword matches wrapped in <mark>."""
    text = text or ""
    snippet = text
    if keywords:
        m = re.search("|".join(re.escape(k) for k in keywords), text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 90)
            snippet = ("…" if start > 0 else "") + text[start:start + max_len]
        else:
            snippet = text[:max_len]
    else:
        snippet = text[:max_len]
    if len(text) > len(snippet):
        snippet = snippet.rstrip() + "…"
    out = html.escape(snippet)
    for k in sorted(set(keywords), key=len, reverse=True):
        out = re.sub(
            f"({re.escape(html.escape(k))})",
            r"<mark>\1</mark>",
            out,
            flags=re.IGNORECASE,
        )
    return out


def badge(label: str, color: str = "#445", bg: str = "#eef2f7") -> str:
    return (
        f"<span style='background:{bg};color:{color};border-radius:10px;"
        f"padding:1px 8px;font-size:11px;font-weight:600;margin-right:6px;"
        f"white-space:nowrap'>{html.escape(label)}</span>"
    )


# ----------------------------------------------------------------------------
# state / predefined application
# ----------------------------------------------------------------------------
def _init_state():
    defaults = {
        "query_text": "", "capability_label": CAP_LABELS["hybrid"],
        "f_account": "(any)", "f_status": [], "f_type": [],
        "f_upd_en": False, "f_upd_date": dt.date(2025, 12, 25),
        "f_exp_en": False, "f_exp_from": dt.date(2026, 1, 1),
        "f_exp_to": dt.date(2027, 1, 1),
        "f_prefix": "", "f_clause_type": "(any)", "f_clause_contains": "",
        "active_note": "", "compare": False, "top_k": 8, "do_search": True,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def apply_predefined():
    label = st.session_state.sel_label
    if label == "✏️ Custom query…":
        st.session_state.active_note = ""
        st.session_state.do_search = False
        return
    pq = next(p for p in PREDEFINED_QUERIES if p["label"] == label)
    f = pq.get("filters", {})
    st.session_state.query_text = pq["query"]
    st.session_state.capability_label = CAP_LABELS[pq["capability"]]
    st.session_state.active_note = pq["note"]
    # reset filters
    st.session_state.f_account = f.get("account", "(any)")
    st.session_state.f_status = list(f.get("status", []))
    st.session_state.f_type = list(f.get("type", []))
    st.session_state.f_prefix = f.get("prefix", "")
    st.session_state.f_clause_type = f.get("clause_type", "(any)")
    st.session_state.f_clause_contains = f.get("clause_contains", "")
    st.session_state.f_upd_en = "updated_from" in f
    if "updated_from" in f:
        st.session_state.f_upd_date = dt.date.fromisoformat(f["updated_from"])
    st.session_state.f_exp_en = "expiring_from" in f or "expiring_to" in f
    if "expiring_from" in f:
        st.session_state.f_exp_from = dt.date.fromisoformat(f["expiring_from"])
    if "expiring_to" in f:
        st.session_state.f_exp_to = dt.date.fromisoformat(f["expiring_to"])
    st.session_state.do_search = True


def collect_filters() -> dict:
    f = {}
    if st.session_state.f_account != "(any)":
        f["account"] = st.session_state.f_account
    if st.session_state.f_status:
        f["status"] = st.session_state.f_status
    if st.session_state.f_type:
        f["type"] = st.session_state.f_type
    if st.session_state.f_upd_en:
        f["updated_from"] = st.session_state.f_upd_date.isoformat()
    if st.session_state.f_exp_en:
        f["expiring_from"] = st.session_state.f_exp_from.isoformat()
        f["expiring_to"] = st.session_state.f_exp_to.isoformat()
    if st.session_state.f_prefix:
        f["prefix"] = st.session_state.f_prefix
    if st.session_state.f_clause_type != "(any)":
        f["clause_type"] = st.session_state.f_clause_type
    if st.session_state.f_clause_contains:
        f["clause_contains"] = st.session_state.f_clause_contains
    return f


# ----------------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------------
def render_card(r: dict, keywords: list[str]):
    with st.container(border=True):
        top = f"**{r['_rank']}. {r['title']}**"
        if "_similarity" in r:
            top += f" &nbsp; · &nbsp; similarity `{r['_similarity']:.3f}`"
        st.markdown(top)
        scolor = STATUS_COLORS.get(r["status"], "#445")
        badges = (
            badge(r["type"], "#0b3d6b", "#e3eefb")
            + badge(r["status"].upper(), "#fff", scolor)
            + badge(r["accountName"])
            + badge(f"updated {r['lastUpdated']}")
            + badge(f"expires {r['expirationDate']}")
        )
        st.markdown(badges, unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:13px;margin-top:8px;color:#333'>"
            f"{highlight(r['content'], keywords)}</div>",
            unsafe_allow_html=True,
        )
        with st.expander(f"clauses · custom attributes · raw  ({r['id']})"):
            for c in r.get("clauses", []):
                st.markdown(f"**{c['clauseType']}** — {c['text']}")
            if r.get("customAttributes"):
                st.markdown("**Attributes:** " + " · ".join(
                    f"{a['name']}: {a['value']}" for a in r["customAttributes"]))
            st.code(json.dumps(
                {k: v for k, v in r.items() if not k.startswith("_")
                 and k != "contentVector"},
                indent=2), language="json")


# ----------------------------------------------------------------------------
# app
# ----------------------------------------------------------------------------
_init_state()

st.title("🔎 Advanced Search on Azure Cosmos DB for NoSQL")
st.caption(
    "Docusign-domain POC · agreements & envelopes · **full-text (BM25)**, "
    "**vector (DiskANN)** and **hybrid (RRF)** search running natively on Cosmos DB, "
    "with an Azure OpenAI RAG agent."
)

with st.sidebar:
    st.header("⚙️ Controls")
    try:
        n = cached_count()
        st.success(f"Connected · {n} agreements in Cosmos DB", icon="✅")
    except Exception as e:  # pragma: no cover
        st.error(f"Cosmos DB connection failed: {e}", icon="🚨")
        st.stop()

    mode = st.radio("Mode", ["🔎 Search Explorer", "📊 Analytics (facets)",
                             "🤖 Ask Copilot (RAG)"],
                    label_visibility="collapsed")
    st.divider()

if mode == "🔎 Search Explorer":
    with st.sidebar:
        labels = ["✏️ Custom query…"] + [p["label"] for p in PREDEFINED_QUERIES]
        st.selectbox("Predefined scenario", labels, key="sel_label",
                     on_change=apply_predefined,
                     index=1)  # default to first scenario
        if "sel_label" in st.session_state and not st.session_state.active_note \
                and st.session_state.query_text == "":
            apply_predefined()

        st.text_area("Query text", key="query_text", height=70,
                     placeholder="Type a search… (free text for vector/hybrid)")
        st.radio("Search capability", list(CAP_LABELS.values()),
                 key="capability_label", horizontal=False)
        st.checkbox("Compare all three capabilities side by side", key="compare")
        st.slider("Results (TOP K)", 3, 15, key="top_k")

        with st.expander("🔧 Filters (boolean + range + nested)"):
            st.selectbox("Account", ACCOUNT_OPTS, key="f_account",
                         format_func=lambda a: ACCOUNTS.get(a, a))
            st.multiselect("Status", STATUSES, key="f_status")
            st.multiselect("Type", TYPES, key="f_type")
            st.checkbox("Updated on/after", key="f_upd_en")
            st.date_input("…date", key="f_upd_date", label_visibility="collapsed")
            st.checkbox("Expiring between", key="f_exp_en")
            c1, c2 = st.columns(2)
            c1.date_input("from", key="f_exp_from")
            c2.date_input("to", key="f_exp_to")
            st.text_input("Title prefix (typeahead)", key="f_prefix")
            st.selectbox("Clause type (nested)", ["(any)"] + CLAUSE_TYPES,
                         key="f_clause_type")
            st.text_input("Clause contains", key="f_clause_contains")

        run = st.button("🔍 Run search", type="primary", use_container_width=True)

    if st.session_state.active_note:
        st.info(st.session_state.active_note, icon="💡")

    capability = LABEL_TO_CAP[st.session_state.capability_label]
    query = st.session_state.query_text.strip()
    filters = collect_filters()
    filters_json = json.dumps(filters, sort_keys=True)

    do = run or st.session_state.do_search
    st.session_state.do_search = False

    if (capability in ("vector", "hybrid")) and not query:
        st.warning("Vector and hybrid search need query text. Add a query or switch "
                   "to Full-text for filter-only searches.", icon="⚠️")
    elif do:
        if st.session_state.compare:
            st.subheader("Side-by-side capability comparison")
            cols = st.columns(3)
            for col, cap in zip(cols, CAP_ORDER):
                with col:
                    st.markdown(f"#### {CAP_LABELS[cap]}")
                    if cap in ("vector", "hybrid") and not query:
                        st.caption("needs query text")
                        continue
                    try:
                        res = cached_search(cap, query, filters_json,
                                            st.session_state.top_k)
                    except Exception as e:
                        st.error(str(e)[:200])
                        continue
                    for r in res["results"]:
                        sim = f" · {r['_similarity']:.2f}" if "_similarity" in r else ""
                        st.markdown(
                            f"<div style='font-size:12.5px;padding:4px 0;"
                            f"border-bottom:1px solid #eee'><b>{r['_rank']}.</b> "
                            f"{html.escape(r['title'])}"
                            f"<span style='color:#888'>{sim}</span></div>",
                            unsafe_allow_html=True)
            st.caption("Notice how vector/hybrid surface conceptually-related "
                       "agreements that pure keyword search can miss.")
        else:
            with st.spinner("Querying Cosmos DB…"):
                res = cached_search(capability, query, filters_json,
                                    st.session_state.top_k)
            eff = res["effective_capability"]
            note = ""
            if eff != capability:
                note = f"  (auto-adjusted to **{CAP_LABELS[eff]}** for this input)"
            st.subheader(f"{len(res['results'])} results · {CAP_LABELS[eff]}{note}",
                         anchor=False)
            if res["keywords"]:
                st.caption("Full-text keywords: " + ", ".join(
                    f"`{k}`" for k in res["keywords"]))
            st.markdown("**Equivalent Cosmos DB SQL**")
            st.code(res["sql"], language="sql")
            for r in res["results"]:
                render_card(r, res["keywords"])
            if not res["results"]:
                st.info("No matches for these filters.")

elif mode == "📊 Analytics (facets)":
    st.subheader("📊 Faceted analytics over agreements", anchor=False)
    st.caption("Native Cosmos DB **`GROUP BY` aggregations** (the Elasticsearch "
               "facets/aggregations feature) plus a date histogram and a "
               "`COUNT(DISTINCT)` cardinality estimate — each with its SQL.")

    with st.sidebar:
        acct = st.selectbox("Scope to account", ["(all accounts)"] + list(ACCOUNTS),
                            format_func=lambda a: ACCOUNTS.get(a, a))
    afilters = {} if acct == "(all accounts)" else {"account": acct}
    afilters_json = json.dumps(afilters, sort_keys=True)

    # metric row
    m = st.columns(4)
    m[0].metric("Agreements", cached_total(afilters_json))
    m[1].metric("Distinct types", cached_distinct("type")["value"])
    m[2].metric("Distinct accounts", cached_distinct("accountId")["value"])
    m[3].metric("Distinct statuses", cached_distinct("status")["value"])

    def facet_chart(title: str, group_expr: str, color: str):
        res = cached_aggregate(group_expr, afilters_json)
        df = pd.DataFrame(res["buckets"])
        st.markdown(f"**{title}**")
        if not df.empty:
            st.bar_chart(df.set_index("key")["count"], color=color, height=240)
        with st.expander("Equivalent Cosmos DB SQL"):
            st.code(res["sql"], language="sql")

    c1, c2 = st.columns(2)
    with c1:
        facet_chart("By agreement type", "c.type", "#0a7bbd")
        facet_chart("By account", "c.accountName", "#7048e8")
    with c2:
        facet_chart("By status", "c.status", "#1a9e54")
        facet_chart("By folder", "c.folderType", "#b35900")

    st.divider()
    st.markdown("**Agreements updated per month** (date histogram via `LEFT(c.lastUpdated, 7)`)")
    hres = cached_histogram("lastUpdated", 7, afilters_json)
    hdf = pd.DataFrame(hres["buckets"])
    if not hdf.empty:
        st.bar_chart(hdf.set_index("key")["count"], color="#134074", height=260)
    with st.expander("Equivalent Cosmos DB SQL"):
        st.code(hres["sql"], language="sql")
    st.caption("Cardinality (`COUNT(DISTINCT)`) is not a native single-query function "
               "in Cosmos DB; the metrics above use the documented DISTINCT-subquery "
               "pattern: `SELECT VALUE COUNT(1) FROM (SELECT DISTINCT VALUE c.type FROM c)`.")

else:  # ---------------- Agent mode ----------------
    import agent

    st.subheader("🤖 Contract Copilot", anchor=False)
    st.caption("Ask in natural language. The agent retrieves with **Cosmos DB hybrid "
               "search**, then answers with the **Azure OpenAI Responses API**, citing "
               "the agreements it used.")
    with st.sidebar:
        pick = st.selectbox("Suggested questions", ["—"] + AGENT_SUGGESTIONS)
        topk = st.slider("Agreements to retrieve", 3, 10, 6)
    default_q = pick if pick != "—" else AGENT_SUGGESTIONS[0]
    question = st.text_input("Your question", value=default_q)
    if st.button("Ask", type="primary"):
        with st.spinner("Retrieving from Cosmos DB and reasoning…"):
            out = agent.answer(question, top_k=topk)
        st.markdown("### Answer")
        st.markdown(out["answer"])
        with st.expander("🔍 Retrieved agreements + the Cosmos DB hybrid query", expanded=False):
            st.code(out["sql"], language="sql")
            for r in out["results"]:
                st.markdown(
                    f"- **{r['id']}** · {r['title']}  "
                    f"<span style='color:#888'>({r['type']}, {r['status']})</span>",
                    unsafe_allow_html=True)
