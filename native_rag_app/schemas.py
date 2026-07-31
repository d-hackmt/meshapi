"""Build order: 05/09.

Pydantic request/response models for the JSON API.

FastAPI uses these to validate incoming request bodies, serialize responses, and
auto-generate the OpenAPI docs. Keeping them in one place documents the exact
shape of every endpoint's input and output.
"""

from pydantic import BaseModel


class Source(BaseModel):
    """One retrieved knowledge-base chunk that grounded the answer."""

    title: str      # source document title (shown as the citation label)
    text: str       # the chunk text used as context
    score: float    # similarity score from the RAG search (higher = closer)


class AskRequest(BaseModel):
    """Body of POST /api/ask (a typed question)."""

    question: str
    top_k: int | None = None   # how many chunks to retrieve; None -> config default
    speak: bool = False        # if True, also return spoken audio of the answer


class AskResponse(BaseModel):
    """Response of POST /api/ask."""

    answer: str
    sources: list[Source]
    audio_base64: str | None = None   # base64 mp3, present only when speak=True


class VoiceAskResponse(BaseModel):
    """Response of POST /api/ask-voice (spoken question in, spoken answer out).

    Always includes audio and echoes back the transcribed `question` so the UI
    can show what it heard.
    """

    question: str
    answer: str
    sources: list[Source]
    audio_base64: str   # base64 mp3 of the answer (always produced for voice)


class IngestResponse(BaseModel):
    """Response of POST /api/ingest -- how many docs uploaded vs. ready to search."""

    documents_uploaded: int
    embedded_ready: int
