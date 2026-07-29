import time

from pinecone import Pinecone, ServerlessSpec

from .config import settings

_pc = Pinecone(api_key=settings.pinecone_api_key)


def get_index():
    existing = [idx["name"] for idx in _pc.list_indexes()]
    if settings.pinecone_index_name not in existing:
        _pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.jina_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
        while not _pc.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)
    return _pc.Index(settings.pinecone_index_name)


def upsert_chunks(vectors: list[dict]) -> None:
    get_index().upsert(vectors=vectors)


def query(vector: list[float], top_k: int) -> list[dict]:
    results = get_index().query(vector=vector, top_k=top_k, include_metadata=True)
    return results["matches"]


def stats() -> dict:
    return get_index().describe_index_stats()
