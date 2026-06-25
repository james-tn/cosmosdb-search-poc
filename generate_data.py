"""LLM-powered sample-data generator.

Uses an Azure OpenAI chat deployment to synthesize additional, realistic (but entirely
fictional) agreement-management contracts that match the schema in `data_gen.py`. The output
is written to `data/generated_agreements.json`, which `build_index.py` merges with the
curated set. Committing that file keeps the corpus reproducible without re-calling the
model; re-run this script any time you want to refresh or expand it.

Usage:
    python generate_data.py --count 20            # generate 20 extra agreements
    python generate_data.py --count 30 --seed 7   # vary the mix
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import sys

import config
from data_gen import ACCOUNTS, AGREEMENTS

TYPES = ["NDA", "MSA", "SOW", "OrderForm", "DPA", "Lease", "Employment",
         "Vendor", "Amendment", "RenewalNotice"]
STATUSES = ["completed", "sent", "delivered", "declined", "voided"]
FOLDERS = ["Completed", "Sent", "Inbox", "Trash"]
CLAUSE_TYPES = ["Auto-Renewal", "Price Escalation", "Service Level",
                "Limitation of Liability", "Confidentiality", "Data Protection",
                "Termination", "Indemnification", "Governing Law"]

OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "generated_agreements.json")

SYSTEM = (
    "You generate realistic but entirely fictional B2B contract metadata for a search "
    "demo in the agreement / contract-management domain. Output strict JSON only. "
    "Do not include real company names, real people, or any real personal data."
)

USER_TMPL = """Generate {n} diverse, realistic agreement records as a JSON object of the form:
{{"agreements": [ {{ ...record... }} ]}}

Each record MUST have exactly these fields:
- "title": short contract title (string)
- "type": one of {types}
- "status": one of {statuses}
- "accountId": one of {accounts}
- "folderType": one of {folders}
- "sender": an email like role@company.com (fictional)
- "recipients": array of 1-2 fictional emails
- "createdDate": ISO date "YYYY-MM-DD" between 2024-01-01 and 2026-06-20
- "lastUpdated": ISO date >= createdDate, <= 2026-06-24
- "expirationDate": ISO date strictly after createdDate
- "content": 50-110 words of realistic contract summary prose (no markdown)
- "clauses": array of 1-4 objects {{"clauseType": one of {clauses}, "text": one realistic sentence}}
- "customAttributes": array of 2 objects {{"name": string, "value": string}} (e.g. Contract Value, Region, Category)
- "tags": array of 1-3 lowercase keywords

Make the mix varied across types and statuses. Write natural, specific prose so that both
keyword and semantic search are meaningful. Avoid reusing these existing titles: {avoid}.
Return ONLY the JSON object."""


def _client():
    # chat.completions with JSON mode for robust structured output
    return config.make_openai_client("2024-10-21")


def _coerce_date(s: str, fallback: dt.date) -> dt.date:
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return fallback


def _validate(rec: dict, idx: int) -> dict | None:
    try:
        atype = rec["type"] if rec.get("type") in TYPES else random.choice(TYPES)
        status = rec["status"] if rec.get("status") in STATUSES else random.choice(STATUSES)
        account = rec["accountId"] if rec.get("accountId") in ACCOUNTS else random.choice(list(ACCOUNTS))
        created = _coerce_date(rec.get("createdDate"), dt.date(2025, 1, 1))
        updated = _coerce_date(rec.get("lastUpdated"), created)
        if updated < created:
            updated = created
        expires = _coerce_date(rec.get("expirationDate"), created + dt.timedelta(days=365))
        if expires <= created:
            expires = created + dt.timedelta(days=365)
        clauses = []
        for c in (rec.get("clauses") or [])[:4]:
            ct = c.get("clauseType")
            if ct not in CLAUSE_TYPES:
                ct = random.choice(CLAUSE_TYPES)
            if c.get("text"):
                clauses.append({"clauseType": ct, "text": str(c["text"]).strip()})
        attrs = [{"name": str(a.get("name", "Attribute")), "value": str(a.get("value", ""))}
                 for a in (rec.get("customAttributes") or [])[:3] if a.get("value")]
        content = str(rec.get("content", "")).strip()
        title = str(rec.get("title", "")).strip()
        if not title or not content:
            return None
        aid = f"agr-{idx:04d}"
        return {
            "id": aid,
            "envelopeId": "env-" + hashlib.md5((aid + title).encode()).hexdigest()[:12],
            "accountId": account,
            "accountName": ACCOUNTS[account],
            "title": title,
            "type": atype,
            "status": status,
            "createdDate": created.isoformat(),
            "lastUpdated": updated.isoformat(),
            "expirationDate": expires.isoformat(),
            "folderId": f"folder-{(rec.get('folderType') or 'Sent').lower()}",
            "folderType": rec.get("folderType") if rec.get("folderType") in FOLDERS else "Sent",
            "sender": str(rec.get("sender", "legal@example.com")),
            "recipients": [str(r) for r in (rec.get("recipients") or ["counterparty@example.com"])][:2],
            "tags": [str(t).lower() for t in (rec.get("tags") or [])][:3],
            "content": content,
            "clauses": clauses or [{"clauseType": "Termination",
                                    "text": "Either party may terminate for material breach."}],
            "customAttributes": attrs or [{"name": "Region", "value": "AMER"}],
        }
    except Exception:
        return None


def generate(count: int, seed: int | None = None) -> list[dict]:
    if seed is not None:
        random.seed(seed)
    avoid = ", ".join(d["title"] for d in AGREEMENTS[:12])
    start_idx = len(AGREEMENTS) + 1  # continue id numbering after curated set
    client = _client()
    out: list[dict] = []
    BATCH = 8
    next_idx = start_idx
    remaining = count
    while remaining > 0:
        n = min(BATCH, remaining)
        prompt = USER_TMPL.format(
            n=n, types=TYPES, statuses=STATUSES, accounts=list(ACCOUNTS),
            folders=FOLDERS, clauses=CLAUSE_TYPES, avoid=avoid,
        )
        resp = client.chat.completions.create(
            model=config.CHAT_DEPLOYMENT,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        data = json.loads(resp.choices[0].message.content)
        recs = data.get("agreements") or data.get("records") or []
        for rec in recs:
            v = _validate(rec, next_idx)
            if v:
                out.append(v)
                next_idx += 1
        print(f"  generated {len(out)}/{count}")
        remaining = count - len(out)
        if not recs:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate extra sample agreements via Azure OpenAI.")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    print(f"Generating {args.count} agreements with '{config.CHAT_DEPLOYMENT}'…")
    docs = generate(args.count, args.seed)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(docs, f, indent=2)
    print(f"Wrote {len(docs)} agreements to {OUT_PATH}")
    print("Now run:  python build_index.py   (it merges curated + generated data)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
