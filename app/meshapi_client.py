from meshapi import ChatCompletionParams, ChatMessage, MeshAPI

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


def list_model_ids(provider: str) -> list[str]:
    resp = _client.models.list(provider=provider)
    items = getattr(resp, "data", resp)
    return [m.id for m in items]
