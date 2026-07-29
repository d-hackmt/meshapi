from pydantic import BaseModel


class Source(BaseModel):
    title: str
    text: str
    score: float


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class IngestResponse(BaseModel):
    chunks_indexed: int
