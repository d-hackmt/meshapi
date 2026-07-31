import json
import time
from pathlib import Path

from . import meshapi_client
from .config import settings
from .data import KNOWLEDGE_BASE

# MeshAPI's RAG file store is account-wide, not scoped per app or per index --
# every upload made with this API key (past runs, other demos, this one) lands in
# the same searchable pool, and files can't be deleted via the API. Without
# tracking our own file_ids and passing them back on every search, results would
# get polluted by whatever else has ever been uploaded with this key. This file
# remembers the file_ids from the most recent ingest() so retrieve() can scope to
# just those.
_STATE_FILE = Path(__file__).resolve().parent / ".rag_state.json"


def _save_file_ids(file_ids: list[str]) -> None:
    _STATE_FILE.write_text(json.dumps({"file_ids": file_ids}))


def _load_file_ids() -> list[str] | None:
    if not _STATE_FILE.exists():
        return None
    return json.loads(_STATE_FILE.read_text()).get("file_ids")


def ingest() -> tuple[int, int]:
    """Upload the sample knowledge base to MeshAPI's managed RAG store and wait
    briefly for embedding to finish. Returns (documents_uploaded, embedded_ready).

    Docs not yet "ready" when the wait window ends still finish embedding in the
    background -- they'll just be missing from search results until then.
    """
    file_ids = [
        meshapi_client.upload_document(
            file_name=f"{doc['id']}.txt",
            mime_type="text/plain",
            content=doc["text"].encode("utf-8"),
            metadata={"title": doc["title"], "doc_id": doc["id"]},
        )
        for doc in KNOWLEDGE_BASE
    ]
    _save_file_ids(file_ids)

    pending = set(file_ids)
    for _ in range(20):
        if not pending:
            break
        time.sleep(3)
        pending = {fid for fid in pending if meshapi_client.embedding_status(fid) not in ("ready", "failed")}

    return len(file_ids), len(file_ids) - len(pending)


def retrieve(query_text: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.rag_top_k
    return meshapi_client.search(query_text, top_k, file_ids=_load_file_ids())


def answer(question: str, model: str | None = None, top_k: int | None = None) -> tuple[str, list[dict]]:
    hits = retrieve(question, top_k=top_k)
    context = "\n\n".join(f"[{h['title']}] {h['text']}" for h in hits)
    prompt = f"""Answer the question using ONLY the context below. If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}"""
    text = meshapi_client.ask(prompt, model=model, temperature=0.2, max_tokens=400)
    return text, hits
