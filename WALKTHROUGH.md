# Guided demo walkthrough

A ~10-minute script for showing the POC. Each step names what to click, what to point out,
and the underlying Cosmos DB capability. Launch with `streamlit run app.py` and open
`http://localhost:8501`.

> The sidebar shows a green **Connected · N agreements in Cosmos DB** badge — every result
> on screen is a live query against a real Azure Cosmos DB for NoSQL container.

---

## 0. Framing (30s)

> "Search runs **inside Cosmos DB** — the same database that stores the agreements. There is
> no separate search cluster, no sync pipeline. We'll cover the capabilities you have today
> in Elasticsearch, then the AI-native features that go beyond it."

---

## 1. Text + range in one query — the headline parity feature (1–2 min)

* Mode: **🔎 Search Explorer**. Scenario: **"'AWS renewal' updated in the last 6 months"**.
* Point out the **💡 teaching note** and the **Equivalent Cosmos DB SQL** panel:
  `ORDER BY RANK FullTextScore(c.content,'aws','renewal')` **with** `WHERE c.lastUpdated >= …`.
* Note the **highlighted** keywords in each result snippet (app-layer highlighting).

> "Full-text relevance and a metadata range filter in a single query — the exact ES feature
> from the inventory, native in Cosmos DB."

![Search Explorer](img/01-search-explorer.png)

---

## 2. Semantic search — beyond keywords (1–2 min)

* Scenario: **"Confidentiality agreements — by meaning (vector)"**.
* The query text says *"protect sensitive information two companies share before a deal"* —
  it never says "NDA". Results are still all the NDAs / confidentiality letters.

> "This is vector search over a DiskANN index. A legacy keyword engine would miss documents
> that don't contain the search words; semantic search finds them by meaning."

* (Optional) tick **Compare all three capabilities side by side** to show full-text vs
  vector vs hybrid for the same query.

![Compare](img/02-compare.png)

---

## 3. Hybrid (RRF) — best of both (1 min)

* Scenario: **"Cloud uptime / SLA commitments (hybrid RRF)"**.
* SQL panel:
  `ORDER BY RANK RRF(VectorDistance(...), FullTextScore(...,'uptime','availability','sla'))`.

> "Hybrid fuses keyword precision and semantic recall with Reciprocal Rank Fusion — one
> ranked list, the best of both. This is a capability the legacy stack doesn't offer
> natively."

---

## 4. Boolean + range + nested (1–2 min)

* Scenario: **"Completed MSAs for Northwind expiring in 2026"** — open the **🔧 Filters**
  expander to show account / status / type / expiry-range controls and the boolean SQL.
* Scenario: **"Auto-renewal clauses needing 60-day notice"** — shows a nested `EXISTS`
  query over the `clauses[]` array.
* Scenario: **"Typeahead: titles starting with 'Master'"** — `STARTSWITH` prefix search.

> "Complex boolean filters, nested document queries, and typeahead — all parity items,
> all native."

---

## 5. Faceted analytics (1–2 min)

* Mode: **📊 Analytics (facets)**.
* Show the metric row (totals + distinct counts) and the bar charts: **by type, status,
  account, folder**, plus the **per-month date histogram**.
* Expand any **Equivalent Cosmos DB SQL** to show the real `GROUP BY` / `COUNT(1)`.
* Use **Scope to account** in the sidebar to re-aggregate for a single account.

> "Facets and aggregations via native `GROUP BY`. Cardinality uses the documented
> DISTINCT-subquery pattern."

![Analytics](img/03-analytics.png)

---

## 6. Contract Copilot — RAG on operational data (1–2 min)

* Mode: **🤖 Ask Copilot (RAG)**. Pick a suggested question, e.g.
  *"Which agreements auto-renew soon, and how much notice must we give to cancel?"* → **Ask**.
* Point out the grounded answer with **cited agreement ids** and notice periods.
* Expand **"Retrieved agreements + the Cosmos DB hybrid query"** to show that the answer is
  grounded in a live hybrid retrieval.

> "Because search lives with the data, you can layer GenAI directly on top: hybrid retrieval
> feeds the Azure OpenAI Responses API to produce grounded, cited answers — RAG with no extra
> data movement."

![Copilot](img/04-agent.png)

---

## 7. Close (30s)

> "Everything you saw is one Cosmos DB container: keyword, semantic and hybrid search,
> filters, nested queries, aggregations, and a RAG agent — no separate search service to run
> or keep in sync, and AI-native capabilities ready for what comes next."

---

### Reset / re-seed

```bash
python build_index.py                 # re-load curated + generated agreements
python generate_data.py --count 25    # synthesize more, then build_index.py again
```
