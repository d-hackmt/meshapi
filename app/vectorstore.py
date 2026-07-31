import time

from pinecone import Pinecone, ServerlessSpec

from .config import settings

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = None


def get_index():
    """Cached after first call -- avoids re-listing/re-describing the index on every upsert/query."""
    global _index
    if _index is not None:
        return _index

    if settings.pinecone_index_name not in [idx["name"] for idx in _pc.list_indexes()]:
        _pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
        while not _pc.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)

    _index = _pc.Index(settings.pinecone_index_name)
    return _index


def upsert_chunks(vectors: list[dict]) -> None:
    get_index().upsert(vectors=vectors)


def query(vector: list[float], top_k: int) -> list[dict]:
    results = get_index().query(vector=vector, top_k=top_k, include_metadata=True)
    return results["matches"]


def stats() -> dict:
    return get_index().describe_index_stats()
