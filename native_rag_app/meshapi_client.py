from meshapi import ChatCompletionParams, ChatMessage, MeshAPI, ModerationParams, SearchRequest, SpeechParams, TranscriptionParams

from .config import settings

_client = MeshAPI(base_url=settings.meshapi_base_url, token=settings.meshapi_token)


def is_flagged(text: str) -> bool:
    """True if MeshAPI's moderation endpoint flags this text as unsafe."""
    result = _client.moderations.create(ModerationParams(input=text))
    return result.results[0].flagged


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


def upload_document(file_name: str, mime_type: str, content: bytes, metadata: dict | None = None) -> str:
    """Hand a raw document straight to MeshAPI's managed RAG store.

    No chunk_text()/embed()/upsert() step to write ourselves -- MeshAPI chunks,
    embeds, and stores it server-side. Returns the file_id.
    """
    upload = _client.rag.upload_file(
        file_name=file_name, mime_type=mime_type, content=content, embed=True, metadata=metadata
    )
    return upload.file_id


def embedding_status(file_id: str) -> str:
    return _client.rag.get(file_id).embedding_status


def search(query: str, top_k: int, file_ids: list[str] | None = None) -> list[dict]:
    results = _client.rag.search(SearchRequest(query=query, top_k=top_k, file_ids=file_ids))
    return [
        {
            "score": r.score,
            "title": (r.metadata or {}).get("title") or r.file_name,
            "text": r.text,
        }
        for r in results.results
    ]


def transcribe(audio_bytes: bytes, filename: str = "recording.webm") -> str:
    transcript = _client.audio.transcribe(audio_bytes, TranscriptionParams(model=settings.stt_model), filename=filename)
    return transcript.text


def synthesize(text: str) -> bytes:
    return _client.audio.synthesize(
        SpeechParams(input=text, model=settings.tts_model, voice=settings.tts_voice, stream=False)
    )
