"""Synthetic but realistic Docusign-domain sample data + predefined demo queries.

Each "agreement" mirrors how an envelope / agreement document would look in a
Cosmos DB for NoSQL container, including nested `clauses` and `customAttributes`
arrays so we can demonstrate nested queries.
"""
from __future__ import annotations

import hashlib
from typing import Any

ACCOUNTS = {
    "acct-northwind": "Northwind Traders",
    "acct-contoso": "Contoso Ltd",
    "acct-fabrikam": "Fabrikam Inc",
    "acct-adatum": "Adatum Corp",
}


def _env_id(seed: str) -> str:
    return "env-" + hashlib.md5(seed.encode()).hexdigest()[:12]


def _doc(
    n: int,
    account: str,
    title: str,
    atype: str,
    status: str,
    created: str,
    updated: str,
    expires: str,
    folder_type: str,
    sender: str,
    recipients: list[str],
    content: str,
    clauses: list[dict[str, str]],
    attrs: list[dict[str, str]],
    tags: list[str],
) -> dict[str, Any]:
    aid = f"agr-{n:04d}"
    return {
        "id": aid,
        "envelopeId": _env_id(aid + title),
        "accountId": account,
        "accountName": ACCOUNTS[account],
        "title": title,
        "type": atype,
        "status": status,
        "createdDate": created,
        "lastUpdated": updated,
        "expirationDate": expires,
        "folderId": f"folder-{folder_type.lower()}",
        "folderType": folder_type,
        "sender": sender,
        "recipients": recipients,
        "tags": tags,
        "content": content,
        "clauses": clauses,
        "customAttributes": attrs,
    }


# --- clause snippets reused across docs ---
AUTO_RENEW_60 = {
    "clauseType": "Auto-Renewal",
    "text": "This Agreement renews automatically for successive twelve (12) month terms "
    "unless either party gives written notice of non-renewal at least 60 days before "
    "the end of the then-current term.",
}
AUTO_RENEW_30 = {
    "clauseType": "Auto-Renewal",
    "text": "The subscription will renew automatically for additional one-year periods "
    "unless cancelled with at least 30 days written notice prior to the renewal date.",
}
ESCALATION = {
    "clauseType": "Price Escalation",
    "text": "Upon each renewal, fees increase by the greater of 7% or the prevailing "
    "CPI index for the preceding twelve months.",
}
SLA_999 = {
    "clauseType": "Service Level",
    "text": "Provider guarantees 99.9% monthly uptime for the hosted platform. If "
    "availability falls below this threshold, Customer is entitled to service credits "
    "on a sliding scale up to 25% of the monthly fee.",
}
LIABILITY = {
    "clauseType": "Limitation of Liability",
    "text": "Each party's aggregate liability is limited to the fees paid in the twelve "
    "months preceding the claim, excluding breaches of confidentiality.",
}
CONFIDENTIALITY = {
    "clauseType": "Confidentiality",
    "text": "The parties shall hold in strict confidence all non-public information "
    "disclosed in connection with the proposed transaction and use it solely to "
    "evaluate the relationship.",
}
GDPR = {
    "clauseType": "Data Protection",
    "text": "Processor shall process personal data of EU data subjects only on documented "
    "instructions from Controller, implement appropriate technical and organizational "
    "measures, and assist with data subject requests in accordance with the GDPR.",
}
TERMINATION = {
    "clauseType": "Termination",
    "text": "Either party may terminate for material breach not cured within 30 days of "
    "written notice.",
}


AGREEMENTS: list[dict[str, Any]] = [
    _doc(
        1, "acct-northwind",
        "Master Services Agreement – Northwind Cloud Platform",
        "MSA", "completed",
        "2024-03-11", "2026-02-18", "2027-03-10", "Completed",
        "legal@northwind.com",
        ["procurement@contoso.com", "cfo@contoso.com"],
        "This Master Services Agreement governs Contoso's subscription to the Northwind "
        "hosted cloud platform, including provisioning of compute, managed databases and "
        "support. It sets out fees, the service level commitment, auto-renewal terms and "
        "annual price adjustments. The platform is delivered as software-as-a-service with "
        "monthly uptime guarantees and support response targets.",
        [SLA_999, AUTO_RENEW_60, ESCALATION, LIABILITY],
        [{"name": "Contract Value", "value": "$480,000"}, {"name": "Region", "value": "AMER"}],
        ["cloud", "renewal", "saas"],
    ),
    _doc(
        2, "acct-contoso",
        "Mutual Non-Disclosure Agreement (Contoso / Fabrikam)",
        "NDA", "completed",
        "2025-11-02", "2025-11-05", "2027-11-01", "Completed",
        "legal@contoso.com",
        ["bizdev@fabrikam.com"],
        "The parties wish to explore a potential commercial partnership and will exchange "
        "proprietary business, technical and financial information. Each side agrees to keep "
        "the other's sensitive material secret, to limit access to employees with a need to "
        "know, and to use it only to evaluate the opportunity. No license to any intellectual "
        "property is granted.",
        [CONFIDENTIALITY, TERMINATION],
        [{"name": "Deal Stage", "value": "Evaluation"}],
        ["confidentiality", "partnership"],
    ),
    _doc(
        3, "acct-fabrikam",
        "Cloud Subscription Order Form – AWS Renewal 2026",
        "OrderForm", "sent",
        "2026-02-01", "2026-02-20", "2026-12-31", "Sent",
        "sales@fabrikam.com",
        ["it-procurement@adatum.com"],
        "Order form for the annual renewal of Adatum's Amazon Web Services hosting bundle "
        "resold by Fabrikam. Covers EC2 reserved capacity, S3 storage and a managed Kubernetes "
        "add-on. This AWS renewal extends the existing commitment for another year with updated "
        "committed-use discounts.",
        [AUTO_RENEW_30, SLA_999],
        [{"name": "Contract Value", "value": "$220,000"}, {"name": "Cloud", "value": "AWS"}],
        ["aws", "renewal", "cloud"],
    ),
    _doc(
        4, "acct-adatum",
        "Statement of Work – Data Migration to Cloud",
        "SOW", "completed",
        "2025-05-14", "2025-09-30", "2026-05-13", "Completed",
        "delivery@adatum.com",
        ["pmo@northwind.com"],
        "This Statement of Work describes a fixed-fee engagement to migrate Northwind's "
        "on-premises ERP databases to a managed cloud environment, including schema "
        "conversion, data validation and cutover planning. Acceptance criteria and milestone "
        "billing are defined herein.",
        [LIABILITY, TERMINATION],
        [{"name": "Contract Value", "value": "$95,000"}, {"name": "Practice", "value": "Migration"}],
        ["migration", "professional-services"],
    ),
    _doc(
        5, "acct-contoso",
        "Data Processing Addendum – EU Customers",
        "DPA", "completed",
        "2025-12-09", "2026-01-15", "2028-12-08", "Completed",
        "privacy@contoso.com",
        ["dpo@northwind.com"],
        "This addendum supplements the master agreement and governs how personal data "
        "belonging to European Union customers is handled. It designates Northwind as the "
        "processor and Contoso as the controller, sets out security measures, sub-processor "
        "rules and breach notification timelines, and incorporates the standard contractual "
        "clauses for international transfers.",
        [GDPR, LIABILITY],
        [{"name": "Region", "value": "EMEA"}, {"name": "Regulation", "value": "GDPR"}],
        ["gdpr", "privacy", "compliance"],
    ),
    _doc(
        6, "acct-northwind",
        "Master Subscription Agreement – Analytics Suite",
        "MSA", "completed",
        "2024-08-22", "2026-03-02", "2026-08-21", "Completed",
        "legal@northwind.com",
        ["ops@fabrikam.com"],
        "Master subscription agreement for the Northwind analytics suite delivered over the "
        "web. Includes a 99.9% availability commitment, automatic annual renewal and a fee "
        "uplift on each renewal. Customer may purchase additional capacity via order forms.",
        [SLA_999, AUTO_RENEW_60, ESCALATION],
        [{"name": "Contract Value", "value": "$360,000"}, {"name": "Region", "value": "AMER"}],
        ["saas", "analytics", "renewal"],
    ),
    _doc(
        7, "acct-fabrikam",
        "One-Way Confidentiality Letter – Acquisition Talks",
        "NDA", "delivered",
        "2026-04-03", "2026-04-04", "2027-04-02", "Sent",
        "corpdev@fabrikam.com",
        ["founders@adatum.com"],
        "In connection with exploratory discussions about a possible acquisition, the "
        "receiving party agrees to safeguard all material shared by the disclosing party, "
        "including roadmaps, customer lists and unaudited financials, and to return or destroy "
        "it if talks end. The information may be used only to assess the proposed deal.",
        [CONFIDENTIALITY],
        [{"name": "Deal Stage", "value": "Due Diligence"}],
        ["confidentiality", "m&a"],
    ),
    _doc(
        8, "acct-adatum",
        "Office Lease Agreement – Seattle HQ",
        "Lease", "completed",
        "2024-01-15", "2024-02-01", "2029-01-31", "Completed",
        "facilities@adatum.com",
        ["leasing@property-co.com"],
        "Commercial lease for 18,000 square feet of office space in downtown Seattle. Sets "
        "the base rent, annual rent escalations, the operating expense pass-through and the "
        "tenant improvement allowance. The term runs five years with one renewal option.",
        [ESCALATION, TERMINATION],
        [{"name": "Contract Value", "value": "$2,150,000"}, {"name": "Region", "value": "AMER"}],
        ["real-estate", "lease"],
    ),
    _doc(
        9, "acct-contoso",
        "Employment Offer Letter – Senior Engineer",
        "Employment", "completed",
        "2026-05-20", "2026-05-22", "2026-07-01", "Completed",
        "people@contoso.com",
        ["candidate@example.com"],
        "Offer of full-time employment for the position of Senior Software Engineer, setting "
        "out base salary, signing bonus, equity grant, benefits and the at-will nature of the "
        "relationship. The offer is contingent on a background check and signing the company's "
        "confidentiality and invention assignment agreement.",
        [CONFIDENTIALITY],
        [{"name": "Department", "value": "Engineering"}],
        ["hr", "offer"],
    ),
    _doc(
        10, "acct-northwind",
        "Vendor Services Agreement – Managed Security",
        "Vendor", "sent",
        "2026-06-10", "2026-06-12", "2027-06-09", "Sent",
        "security@northwind.com",
        ["sales@secureops.com"],
        "Agreement engaging a third-party vendor to provide 24x7 managed security monitoring, "
        "incident response and quarterly penetration testing. Defines response-time service "
        "levels, data handling obligations and the right to audit the vendor's controls.",
        [SLA_999, GDPR, TERMINATION],
        [{"name": "Contract Value", "value": "$140,000"}, {"name": "Category", "value": "Security"}],
        ["vendor", "security"],
    ),
    _doc(
        11, "acct-fabrikam",
        "Master Services Agreement – Consulting (Fabrikam)",
        "MSA", "declined",
        "2025-10-01", "2025-10-18", "2026-09-30", "Sent",
        "legal@fabrikam.com",
        ["procurement@contoso.com"],
        "Umbrella consulting agreement under which individual statements of work may be "
        "issued for advisory and implementation services. Covers rate cards, expense policy, "
        "intellectual property ownership of deliverables and a mutual limitation of liability. "
        "The counterparty declined pending changes to the IP terms.",
        [LIABILITY, TERMINATION],
        [{"name": "Practice", "value": "Advisory"}],
        ["consulting", "declined"],
    ),
    _doc(
        12, "acct-adatum",
        "Subscription Order Form – Collaboration Suite",
        "OrderForm", "completed",
        "2025-12-28", "2026-01-03", "2027-01-02", "Completed",
        "it@adatum.com",
        ["sales@northwind.com"],
        "Order form for 500 seats of the Northwind collaboration suite, billed annually. The "
        "subscription renews automatically each year and the per-seat price rises on renewal. "
        "Includes standard support and a 99.9% uptime target.",
        [AUTO_RENEW_30, ESCALATION, SLA_999],
        [{"name": "Contract Value", "value": "$72,000"}, {"name": "Seats", "value": "500"}],
        ["saas", "renewal"],
    ),
    _doc(
        13, "acct-contoso",
        "Amendment No. 2 – Pricing Update to MSA",
        "Amendment", "completed",
        "2026-03-15", "2026-03-19", "2027-03-14", "Completed",
        "legal@contoso.com",
        ["legal@northwind.com"],
        "Second amendment to the master services agreement that revises the fee schedule, "
        "adds a new environment and confirms that the automatic renewal and price escalation "
        "provisions remain in effect for the extended term.",
        [ESCALATION, AUTO_RENEW_60],
        [{"name": "Parent Agreement", "value": "agr-0001"}],
        ["amendment", "pricing"],
    ),
    _doc(
        14, "acct-northwind",
        "Non-Disclosure Agreement – Joint Product Pilot",
        "NDA", "completed",
        "2026-01-22", "2026-01-23", "2027-01-21", "Completed",
        "legal@northwind.com",
        ["product@contoso.com"],
        "Reciprocal agreement to protect information swapped while the two companies run a "
        "joint pilot of an unreleased product. Covers source code, designs and performance "
        "data, with confidentiality surviving three years past termination.",
        [CONFIDENTIALITY, TERMINATION],
        [{"name": "Deal Stage", "value": "Pilot"}],
        ["confidentiality", "pilot"],
    ),
    _doc(
        15, "acct-fabrikam",
        "Cloud Hosting Agreement – Azure Workloads",
        "MSA", "completed",
        "2025-07-08", "2026-02-27", "2026-07-07", "Completed",
        "cloud@fabrikam.com",
        ["it@adatum.com"],
        "Agreement covering the hosting of Adatum's production workloads on a managed Azure "
        "footprint operated by Fabrikam. Specifies the availability guarantee, disaster "
        "recovery commitments, the shared responsibility model and an automatic annual "
        "renewal with notice requirements.",
        [SLA_999, AUTO_RENEW_60, LIABILITY],
        [{"name": "Contract Value", "value": "$310,000"}, {"name": "Cloud", "value": "Azure"}],
        ["cloud", "azure", "renewal"],
    ),
    _doc(
        16, "acct-adatum",
        "Data Processing Agreement – Marketing Platform",
        "DPA", "sent",
        "2026-05-30", "2026-06-02", "2028-05-29", "Sent",
        "privacy@adatum.com",
        ["dpo@fabrikam.com"],
        "Processing terms for a marketing automation platform that handles contact records "
        "and behavioural data of European prospects. Establishes the lawful basis, retention "
        "limits, security controls and the obligations of the processor to support audits and "
        "data subject access requests under European privacy law.",
        [GDPR],
        [{"name": "Region", "value": "EMEA"}, {"name": "Regulation", "value": "GDPR"}],
        ["gdpr", "privacy", "marketing"],
    ),
    _doc(
        17, "acct-contoso",
        "Master Software License Agreement – On-Prem",
        "MSA", "completed",
        "2024-11-19", "2025-11-30", "2026-11-18", "Completed",
        "legal@contoso.com",
        ["licensing@fabrikam.com"],
        "Perpetual on-premises software license with annual maintenance. Grants the right to "
        "use the software internally, sets the maintenance fee that increases each year, and "
        "limits liability. Maintenance renews automatically unless cancelled.",
        [AUTO_RENEW_30, ESCALATION, LIABILITY],
        [{"name": "Contract Value", "value": "$200,000"}, {"name": "License", "value": "Perpetual"}],
        ["license", "on-prem"],
    ),
    _doc(
        18, "acct-northwind",
        "Reseller Agreement – Channel Partner",
        "Vendor", "voided",
        "2025-02-10", "2025-03-01", "2026-02-09", "Trash",
        "channel@northwind.com",
        ["partners@contoso.com"],
        "Agreement appointing the counterparty as a non-exclusive reseller of Northwind "
        "products, including margins, marketing obligations and territory. The agreement was "
        "voided before countersignature.",
        [TERMINATION],
        [{"name": "Channel", "value": "Reseller"}],
        ["channel", "voided"],
    ),
    _doc(
        19, "acct-fabrikam",
        "Professional Services SOW – Security Assessment",
        "SOW", "completed",
        "2026-04-18", "2026-05-08", "2026-10-17", "Completed",
        "delivery@fabrikam.com",
        ["security@northwind.com"],
        "Time-and-materials engagement to perform a comprehensive security assessment, "
        "including a penetration test of internet-facing systems, a configuration review and "
        "a prioritised remediation roadmap delivered to the customer's security team.",
        [LIABILITY, TERMINATION],
        [{"name": "Contract Value", "value": "$60,000"}, {"name": "Category", "value": "Security"}],
        ["security", "assessment"],
    ),
    _doc(
        20, "acct-adatum",
        "Enterprise Order Form – AWS Marketplace Renewal",
        "OrderForm", "completed",
        "2026-01-09", "2026-03-05", "2027-01-08", "Completed",
        "procurement@adatum.com",
        ["sales@fabrikam.com"],
        "Renewal order placed through the Amazon Web Services marketplace for a private "
        "offer covering data analytics tooling. This AWS renewal carries a committed annual "
        "spend with marketplace billing and automatic renewal.",
        [AUTO_RENEW_30],
        [{"name": "Contract Value", "value": "$185,000"}, {"name": "Cloud", "value": "AWS"}],
        ["aws", "renewal", "marketplace"],
    ),
    _doc(
        21, "acct-contoso",
        "Mutual NDA – Vendor Onboarding",
        "NDA", "sent",
        "2026-06-15", "2026-06-16", "2027-06-14", "Sent",
        "legal@contoso.com",
        ["sales@secureops.com"],
        "Standard reciprocal secrecy terms entered before sharing security questionnaires and "
        "architecture details during vendor onboarding. Each party protects the other's "
        "private materials and restricts internal distribution.",
        [CONFIDENTIALITY],
        [{"name": "Deal Stage", "value": "Onboarding"}],
        ["confidentiality", "vendor"],
    ),
    _doc(
        22, "acct-northwind",
        "Master Services Agreement – Support & Maintenance",
        "MSA", "completed",
        "2024-06-30", "2026-04-12", "2026-12-29", "Completed",
        "legal@northwind.com",
        ["it@adatum.com"],
        "Master agreement for premium support and maintenance, including a guaranteed uptime "
        "for the support portal, target response times by severity, automatic annual renewal "
        "and an annual fee increase tied to inflation.",
        [SLA_999, AUTO_RENEW_60, ESCALATION],
        [{"name": "Contract Value", "value": "$128,000"}, {"name": "Tier", "value": "Premium"}],
        ["support", "renewal"],
    ),
    _doc(
        23, "acct-fabrikam",
        "Lease Amendment – Austin Expansion",
        "Amendment", "delivered",
        "2026-02-14", "2026-02-15", "2030-02-13", "Sent",
        "facilities@fabrikam.com",
        ["leasing@property-co.com"],
        "Amendment expanding the leased premises by an additional floor and adjusting the "
        "base rent and escalation schedule accordingly. Confirms the renewal option and the "
        "operating expense methodology carry over to the expanded space.",
        [ESCALATION],
        [{"name": "Region", "value": "AMER"}],
        ["real-estate", "amendment"],
    ),
    _doc(
        24, "acct-adatum",
        "Software-as-a-Service Agreement – HR Platform",
        "MSA", "completed",
        "2025-09-12", "2025-12-31", "2026-09-11", "Completed",
        "people@adatum.com",
        ["sales@northwind.com"],
        "Subscription to a cloud human-resources platform delivered as a service. The terms "
        "include a monthly availability commitment, automatic renewal each year, and a fee "
        "adjustment on renewal. Personal data of employees is processed under an attached "
        "data protection schedule.",
        [SLA_999, AUTO_RENEW_30, GDPR],
        [{"name": "Contract Value", "value": "$54,000"}, {"name": "Module", "value": "HR"}],
        ["saas", "hr", "renewal"],
    ),
    _doc(
        25, "acct-contoso",
        "Statement of Work – Custom Integration",
        "SOW", "sent",
        "2026-06-01", "2026-06-08", "2026-12-01", "Sent",
        "delivery@contoso.com",
        ["pmo@fabrikam.com"],
        "Fixed-price project to build a custom integration between the customer's CRM and the "
        "Northwind billing service, including API development, testing and a hypercare period. "
        "Milestones, acceptance and change-control are defined.",
        [LIABILITY, TERMINATION],
        [{"name": "Contract Value", "value": "$78,000"}, {"name": "Practice", "value": "Integration"}],
        ["integration", "project"],
    ),
    _doc(
        26, "acct-northwind",
        "Confidential Information Exchange – Roadmap Briefing",
        "NDA", "completed",
        "2025-08-05", "2025-08-06", "2026-08-04", "Completed",
        "product@northwind.com",
        ["strategy@contoso.com"],
        "Terms under which the company will brief a strategic customer on its unreleased "
        "product direction. The customer agrees not to disclose the forward-looking plans, to "
        "limit the audience to named individuals, and not to make purchasing decisions in "
        "reliance on the roadmap.",
        [CONFIDENTIALITY],
        [{"name": "Deal Stage", "value": "Strategic"}],
        ["confidentiality", "roadmap"],
    ),
    _doc(
        27, "acct-fabrikam",
        "Managed Services Agreement – Network Operations",
        "MSA", "completed",
        "2024-12-03", "2026-05-22", "2026-12-02", "Completed",
        "noc@fabrikam.com",
        ["it@adatum.com"],
        "Outsourced network operations agreement covering monitoring, patching and capacity "
        "management of the customer's wide-area network. Defines the availability guarantee, "
        "escalation paths, automatic renewal and the annual indexed fee adjustment.",
        [SLA_999, AUTO_RENEW_60, ESCALATION],
        [{"name": "Contract Value", "value": "$240,000"}, {"name": "Category", "value": "Network"}],
        ["managed-services", "renewal"],
    ),
    _doc(
        28, "acct-adatum",
        "Vendor Agreement – Payment Processing",
        "Vendor", "completed",
        "2025-04-27", "2025-12-20", "2027-04-26", "Completed",
        "finance@adatum.com",
        ["sales@paymentsco.com"],
        "Agreement with a payment processor to handle card transactions, setting the fee per "
        "transaction, settlement timing, PCI-DSS compliance obligations and the handling of "
        "cardholder data. Includes audit rights and breach notification duties.",
        [GDPR, LIABILITY, TERMINATION],
        [{"name": "Category", "value": "Payments"}, {"name": "Compliance", "value": "PCI-DSS"}],
        ["payments", "compliance"],
    ),
    _doc(
        29, "acct-contoso",
        "Master Cloud Services Agreement – Multi-Region",
        "MSA", "completed",
        "2025-06-18", "2026-06-01", "2027-06-17", "Completed",
        "legal@contoso.com",
        ["cloud@northwind.com"],
        "Comprehensive cloud services agreement spanning multiple regions, with a strong "
        "availability commitment, regional data-residency options, automatic renewal and a "
        "negotiated cap on annual price increases. Personal data is processed under the "
        "attached European data protection terms.",
        [SLA_999, AUTO_RENEW_60, ESCALATION, GDPR],
        [{"name": "Contract Value", "value": "$540,000"}, {"name": "Region", "value": "Global"}],
        ["cloud", "renewal", "gdpr"],
    ),
    _doc(
        30, "acct-fabrikam",
        "Employment Offer Letter – Sales Director",
        "Employment", "declined",
        "2026-03-09", "2026-03-21", "2026-05-01", "Sent",
        "people@fabrikam.com",
        ["candidate2@example.com"],
        "Offer for the role of Sales Director including base salary, commission plan, equity "
        "and relocation support. The candidate declined the offer. The letter references the "
        "standard confidentiality and non-solicitation obligations.",
        [CONFIDENTIALITY],
        [{"name": "Department", "value": "Sales"}],
        ["hr", "offer", "declined"],
    ),
]


def embedding_text(doc: dict[str, Any]) -> str:
    """Compose the text that gets embedded into the content vector."""
    clause_text = " ".join(c["text"] for c in doc.get("clauses", []))
    attr_text = " ".join(f"{a['name']}: {a['value']}" for a in doc.get("customAttributes", []))
    return (
        f"{doc['title']} ({doc['type']}). {doc['content']} "
        f"Clauses: {clause_text} Attributes: {attr_text}"
    )


# -------------------------------------------------------------------------
# Predefined demo queries. `capability` is one of fulltext | vector | hybrid.
# Filters use ISO date strings (inclusive lower / exclusive upper where noted).
# -------------------------------------------------------------------------
PREDEFINED_QUERIES: list[dict[str, Any]] = [
    {
        "id": "text_range_aws_renewal",
        "label": "📅  'AWS renewal' updated in the last 6 months  (full-text + range)",
        "capability": "fulltext",
        "query": "AWS renewal",
        "filters": {"updated_from": "2025-12-25"},
        "note": "The headline Elasticsearch feature — full-text search **and** a metadata range "
        "filter in a single query (\u201cdocs containing 'AWS renewal' updated in the last 6 "
        "months\u201d). Cosmos DB reaches this natively.",
    },
    {
        "id": "semantic_nda",
        "label": "🔒  Confidentiality agreements — by meaning  (vector / semantic)",
        "capability": "vector",
        "query": "protect sensitive information two companies share before a possible deal",
        "filters": {},
        "note": "Pure semantic search. It surfaces NDAs and confidentiality letters even when "
        "the body never uses those exact words — a forward capability **beyond legacy keyword "
        "search**.",
    },
    {
        "id": "hybrid_sla",
        "label": "☁️  Cloud uptime / SLA commitments  (hybrid RRF)",
        "capability": "hybrid",
        "query": "guaranteed service uptime and availability credits for the cloud platform",
        "filters": {},
        "note": "Hybrid fuses BM25 keyword precision ('uptime', 'availability', 'SLA') with "
        "semantic recall via Reciprocal Rank Fusion — the best of both worlds in one ranked list.",
    },
    {
        "id": "boolean_range_msa",
        "label": "✅  Completed MSAs for Northwind expiring in 2026  (boolean + range)",
        "capability": "fulltext",
        "query": "",
        "filters": {
            "account": "acct-northwind",
            "status": ["completed"],
            "type": ["MSA"],
            "expiring_from": "2026-01-01",
            "expiring_to": "2027-01-01",
        },
        "note": "Complex boolean filters combined with a date range, no full-text needed — "
        "demonstrates Elasticsearch 'complex boolean filters' parity.",
    },
    {
        "id": "nested_autorenewal",
        "label": "🔁  Auto-renewal clauses needing 60-day notice  (nested array query)",
        "capability": "fulltext",
        "query": "",
        "filters": {"clause_type": "Auto-Renewal", "clause_contains": "60 days"},
        "note": "Nested query over the `clauses[]` array — find agreements that contain an "
        "Auto-Renewal clause mentioning '60 days'. Cosmos uses `EXISTS` / `JOIN` over the array.",
    },
    {
        "id": "semantic_price_escalation",
        "label": "💸  Contracts that lock us into automatic price increases  (vector)",
        "capability": "vector",
        "query": "terms that automatically raise our fees or renew us at a higher price",
        "filters": {},
        "note": "Concept search with almost no shared keywords. Vector retrieval connects the "
        "idea to escalation / auto-renewal clauses — a lexical engine returns little.",
    },
    {
        "id": "prefix_typeahead",
        "label": "⌨️  Typeahead: titles starting with 'Master'  (prefix)",
        "capability": "fulltext",
        "query": "",
        "filters": {"prefix": "Master"},
        "note": "Search-as-you-type / typeahead via `STARTSWITH(c.title, @prefix)`.",
    },
    {
        "id": "hybrid_dpa_gdpr",
        "label": "🛡️  Data processing & GDPR obligations  (hybrid RRF)",
        "capability": "hybrid",
        "query": "how personal data of EU customers is processed and protected under GDPR",
        "filters": {},
        "note": "Hybrid retrieval for a compliance review — keyword ('GDPR', 'processor') plus "
        "semantic understanding of data-protection language.",
    },
]


AGENT_SUGGESTIONS = [
    "Which agreements auto-renew soon, and how much notice must we give to cancel?",
    "Summarize our confidentiality obligations across the active NDAs.",
    "What cloud uptime/SLA commitments have we made, and what are the remedies if missed?",
    "Which Northwind contracts expire in 2026 and what are their contract values?",
    "Where do we have GDPR data-processing obligations for EU customers?",
]
