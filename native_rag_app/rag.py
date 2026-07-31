"""Build order: 04/09.

RAG orchestration: ingest -> retrieve -> answer.

This is the heart of the app and shows how little code MeshAPI's managed RAG
store needs: upload the docs (MeshAPI chunks + embeds them), search for the
relevant chunks, then feed them to a chat completion. The only real complexity
is working around the account-wide file store (see the note below).
"""

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
    """Persist this run's uploaded file_ids to the local state file."""
    _STATE_FILE.write_text(json.dumps({"file_ids": file_ids}))


def _load_file_ids() -> list[str] | None:
    """Load file_ids saved by the last ingest(), or None if we've never ingested.

    None means "don't scope the search" -- but you should run ingest() first so
    results stay limited to this app's own documents.
    """
    if not _STATE_FILE.exists():
        return None
    return json.loads(_STATE_FILE.read_text()).get("file_ids")


def ingest() -> tuple[int, int]:
    """Upload the sample knowledge base to MeshAPI's managed RAG store and wait
    briefly for embedding to finish. Returns (documents_uploaded, embedded_ready).

    Docs not yet "ready" when the wait window ends still finish embedding in the
    background -- they'll just be missing from search results until then.
    """
    # Upload every KB document as a plain-text file. MeshAPI chunks + embeds each
    # one server-side (embed=True) and returns a file_id we collect.
    file_ids = [
        meshapi_client.upload_document(
            file_name=f"{doc['id']}.txt",
            mime_type="text/plain",
            content=doc["text"].encode("utf-8"),
            metadata={"title": doc["title"], "doc_id": doc["id"]},
        )
        for doc in KNOWLEDGE_BASE
    ]
    # Remember these ids so retrieve() can scope searches to only our data.
    _save_file_ids(file_ids)

    # Poll until every file has finished embedding (or we give up after ~60s).
    # A file is "done" once its status is no longer pending -- i.e. ready/failed.
    pending = set(file_ids)
    for _ in range(20):
        if not pending:
            break
        time.sleep(3)
        pending = {fid for fid in pending if meshapi_client.embedding_status(fid) not in ("ready", "failed")}

    # embedded_ready = how many finished within the wait window.
    return len(file_ids), len(file_ids) - len(pending)


def retrieve(query_text: str, top_k: int | None = None) -> list[dict]:
    """Return the top_k most relevant chunks for a query, scoped to our uploads."""
    top_k = top_k or settings.rag_top_k
    # Passing our own file_ids keeps results from being polluted by other uploads
    # sharing this account's RAG store.
    return meshapi_client.search(query_text, top_k, file_ids=_load_file_ids())


def answer(question: str, model: str | None = None, top_k: int | None = None) -> tuple[str, list[dict]]:
    """Full RAG answer: retrieve context, then ask the LLM using only that context.

    Returns (answer_text, hits) so the caller can show both the answer and the
    source chunks it was grounded in.
    """
    # 1. Retrieve the most relevant chunks for this question.
    hits = retrieve(question, top_k=top_k)
    # 2. Assemble them into a labeled context block ("[Title] chunk text ...").
    context = "\n\n".join(f"[{h['title']}] {h['text']}" for h in hits)
    # 3. Constrain the model to the retrieved context to reduce hallucination.
    prompt = f"""Answer the question using ONLY the context below. If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}"""
    text = meshapi_client.ask(prompt, model=model, temperature=0.2, max_tokens=400)
    return text, hits
