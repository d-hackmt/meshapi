KNOWLEDGE_BASE = [
    {
        "id": "doc-1",
        "title": "Refund Policy",
        "text": "Nimbus Cloud offers a 30-day money-back guarantee on all annual plans. Monthly plans can be cancelled anytime but are not eligible for partial refunds. Refund requests must be submitted through the billing portal within the eligibility window.",
    },
    {
        "id": "doc-2",
        "title": "Storage Limits",
        "text": "The Starter plan includes 100GB of storage, Pro includes 2TB, and Enterprise is negotiated per contract. Exceeding your plan's limit pauses new uploads until you upgrade or free up space; existing files remain accessible.",
    },
    {
        "id": "doc-3",
        "title": "Data Retention",
        "text": "Deleted files move to a Trash folder and are permanently removed after 30 days. Account cancellation triggers a 90-day data retention window before permanent deletion, during which reactivation restores all data.",
    },
    {
        "id": "doc-4",
        "title": "Sharing & Permissions",
        "text": "Files can be shared via link (view or edit access) or invited by email with role-based permissions: Viewer, Commenter, Editor, Owner. Shared links can be password-protected and set to expire after a chosen number of days.",
    },
    {
        "id": "doc-5",
        "title": "Two-Factor Authentication",
        "text": "2FA is optional for Starter and Pro plans but mandatory for all Enterprise accounts. Supported methods are authenticator apps (TOTP) and SMS. Recovery codes are generated once and shown only at setup time.",
    },
    {
        "id": "doc-6",
        "title": "API Rate Limits",
        "text": "The Nimbus Cloud API allows 100 requests per minute on Starter, 1000 on Pro, and custom limits on Enterprise. Exceeding the limit returns HTTP 429 with a Retry-After header indicating when to resume.",
    },
    {
        "id": "doc-7",
        "title": "Plan Downgrades",
        "text": "Downgrading takes effect at the end of the current billing cycle. If your stored data exceeds the new plan's limit, you'll have a 14-day grace period to remove files before uploads are paused.",
    },
    {
        "id": "doc-8",
        "title": "Support Response Times",
        "text": "Starter plan support responds within 48 hours via email. Pro plan support responds within 24 hours and includes live chat. Enterprise customers get a dedicated support contact with a 4-hour SLA.",
    },
]


def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def build_chunks() -> list[dict]:
    chunks = []
    for doc in KNOWLEDGE_BASE:
        for i, c in enumerate(chunk_text(doc["text"])):
            chunks.append({"doc_id": doc["id"], "title": doc["title"], "chunk_index": i, "text": c})
    return chunks
