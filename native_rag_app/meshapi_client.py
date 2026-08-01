"""Build order: 03/09.

Thin wrapper around the MeshAPI SDK.

Every capability this app needs -- chat completions, content moderation, the
managed RAG file store (upload + search), speech-to-text and text-to-speech --
is reached through a *single* ``MeshAPI`` client authenticated with *one* API
key. This module keeps all direct SDK usage in one place so the rest of the app
(rag.py, main.py) talks to small, intention-revealing helper functions instead
of the raw SDK.
"""

import base64

from meshapi import ChatCompletionParams, ChatMessage, MeshAPI, ModerationParams, SearchRequest, SpeechParams, TranscriptionParams

from .config import settings

# One client for the whole app. Constructed once at import time; every helper
# below dispatches off it -- no per-feature client or key.
_client = MeshAPI(base_url=settings.meshapi_base_url, token=settings.meshapi_token)


def is_flagged(text: str) -> bool:
    """Return True if MeshAPI's moderation endpoint flags this text as unsafe.

    Used to screen user questions before we spend a chat call on them.
    """
    result = _client.moderations.create(ModerationParams(input=text))
    # The API returns a list of results (one per input); we send a single string.
    return result.results[0].flagged


def ask(prompt: str, model: str | None = None, temperature: float = 0.2, max_tokens: int = 400) -> str:
    """Run one chat completion and return just the assistant's text.

    The `model` is a MeshAPI "provider/model" string; passing None uses the
    configured default. Low temperature keeps answers grounded/deterministic,
    which suits RAG.
    """
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
    embeds, and stores it server-side. `embed=True` triggers embedding on upload;
    `metadata` (title/doc_id) rides along so search results can be attributed.
    Returns the server-assigned file_id, which we track to scope later searches.
    """
    upload = _client.rag.upload_file(
        file_name=file_name, mime_type=mime_type, content=content, embed=True, metadata=metadata
    )
    return upload.file_id


def embedding_status(file_id: str) -> str:
    """Return the current embedding status of an uploaded file.

    Embedding happens asynchronously after upload; callers poll this until it
    reads "ready" (or "failed"). See rag.ingest.
    """
    return _client.rag.get(file_id).embedding_status


def search(query: str, top_k: int, file_ids: list[str] | None = None) -> list[dict]:
    """Semantic-search the RAG store and return the top matching chunks.

    `file_ids` scopes the search to just our own uploads -- essential because the
    /v1/files store is account-wide (see rag.py's note). We flatten each result
    into a small dict the rest of the app can use without knowing SDK types;
    `title` falls back to the file name if no metadata title was set.
    """
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
    """Speech-to-text: convert recorded audio bytes into a question string."""
    transcript = _client.audio.transcribe(audio_bytes, TranscriptionParams(model=settings.stt_model), filename=filename)
    return transcript.text


def synthesize_base64(text: str) -> str:
    """Text-to-speech: turn an answer string into a base64-encoded mp3.

    Base64-encoded here (not raw bytes) since every caller just hands the result
    straight into a JSON response body.
    """
    audio_bytes = _client.audio.synthesize(
        SpeechParams(input=text, model=settings.tts_model, voice=settings.tts_voice, stream=False)
    )
    return base64.b64encode(audio_bytes).decode()
