from meshapi import ChatCompletionParams, ChatMessage, EmbeddingsParams, MeshAPI

from .config import settings

_client = MeshAPI(base_url=settings.meshapi_base_url, token=settings.meshapi_token)


def ask(prompt: str, model: str | None = None, temperature: float = 0.2, max_tokens: int = 400) -> str:
    resp = _client.chat.completions.create(
        ChatCompletionParams(
            model=model or settings.meshapi_chat_model,
            messages=[ChatMessage(role="user", content=prompt)],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    )
    return resp.choices[0].message.content


def embed(texts: list[str]) -> list[list[float]]:
    resp = _client.embeddings.create(
        EmbeddingsParams(
            model=settings.meshapi_embedding_model,
            input=texts,
            dimensions=settings.embedding_dimensions,
        )
    )
    return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
