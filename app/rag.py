from . import data, meshapi_client, vectorstore
from .config import settings


def ingest() -> int:
    """Chunk the sample knowledge base, embed it via MeshAPI, and upsert into Pinecone."""
    chunks = data.build_chunks()
    vectors = meshapi_client.embed([c["text"] for c in chunks])

    pinecone_vectors = [
        {
            "id": f"{c['doc_id']}-{c['chunk_index']}",
            "values": vector,
            "metadata": {"title": c["title"], "text": c["text"], "doc_id": c["doc_id"]},
        }
        for c, vector in zip(chunks, vectors)
    ]

    vectorstore.upsert_chunks(pinecone_vectors)
    return len(pinecone_vectors)


def retrieve(query_text: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.top_k
    query_vector = meshapi_client.embed([query_text])[0]
    matches = vectorstore.query(query_vector, top_k=top_k)
    return [
        {"score": m["score"], "title": m["metadata"]["title"], "text": m["metadata"]["text"]}
        for m in matches
    ]


def answer(question: str, model: str | None = None, top_k: int | None = None) -> tuple[str, list[dict]]:
    hits = retrieve(question, top_k=top_k)
    context = "\n\n".join(f"[{h['title']}] {h['text']}" for h in hits)
    prompt = f"""Answer the question using ONLY the context below. If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}"""
    text = meshapi_client.ask(prompt, model=model, temperature=0.2, max_tokens=400)
    return text, hits
