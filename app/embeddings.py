import requests

from .config import settings

JINA_URL = "https://api.jina.ai/v1/embeddings"


def embed(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    """Embed a list of strings with Jina Embeddings.

    task: 'retrieval.passage' for documents being indexed, 'retrieval.query' for search queries.
    """
    resp = requests.post(
        JINA_URL,
        headers={
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.jina_model,
            "task": task,
            "dimensions": settings.jina_dimensions,
            "input": texts,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    data.sort(key=lambda d: d["index"])
    return [d["embedding"] for d in data]
