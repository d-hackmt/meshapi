from pydantic import BaseModel


class Source(BaseModel):
    title: str
    text: str
    score: float


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None
    speak: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    audio_base64: str | None = None


class VoiceAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    audio_base64: str


class IngestResponse(BaseModel):
    documents_uploaded: int
    embedded_ready: int
