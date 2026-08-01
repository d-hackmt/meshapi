"""Build order: 06/09.

FastAPI application: HTML page + JSON API for the MeshAPI-native RAG demo.

Wires the pieces together and exposes the HTTP surface:
  GET  /               -> the single-page UI
  POST /api/ingest     -> upload + embed the sample knowledge base
  POST /api/ask        -> answer a typed question (optionally with spoken audio)
  POST /api/ask-voice  -> answer a spoken question (audio in, audio out)

All the actual work lives in rag.py / meshapi_client.py; these handlers just
validate input, call into them, and shape the response.
"""

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import meshapi_client, rag
from .config import settings
from .schemas import AskRequest, AskResponse, IngestResponse, VoiceAskResponse

# Resolve static/ and templates/ relative to this file so the app runs correctly
# no matter what the current working directory is.
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="MeshAPI Native RAG Demo")

# Serve JS/CSS from /static and render index.html via Jinja from /templates.
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _reject_if_flagged(question: str) -> None:
    """Raise a 400 if MeshAPI's moderation endpoint flags this question."""
    if meshapi_client.is_flagged(question):
        raise HTTPException(400, "That question was flagged by content moderation -- try rephrasing.")


@app.on_event("startup")
def on_startup() -> None:
    """Fail fast at boot if the MeshAPI key is missing."""
    settings.validate()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """Serve the single-page UI (form + mic + answer area)."""
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/api/ingest", response_model=IngestResponse)
def api_ingest() -> IngestResponse:
    """Upload the sample knowledge base and report how many docs are search-ready."""
    uploaded, ready = rag.ingest()
    return IngestResponse(documents_uploaded=uploaded, embedded_ready=ready)


@app.post("/api/ask", response_model=AskResponse)
def api_ask(req: AskRequest) -> AskResponse:
    """Answer a typed question, optionally returning spoken audio too."""
    # Screen the question with moderation before spending a chat call on it.
    _reject_if_flagged(req.question)

    # Retrieve + generate the grounded answer.
    answer_text, sources = rag.answer(req.question, top_k=req.top_k)
    # Only synthesize speech when the client asked for it (speak=True).
    audio_b64 = meshapi_client.synthesize_base64(answer_text) if req.speak else None
    return AskResponse(answer=answer_text, sources=sources, audio_base64=audio_b64)


@app.post("/api/ask-voice", response_model=VoiceAskResponse)
async def api_ask_voice(audio: UploadFile = File(...)) -> VoiceAskResponse:
    """Answer a *spoken* question: transcribe -> moderate -> answer -> speak back."""
    # 1. Read the uploaded recording and transcribe it to text (speech-to-text).
    audio_bytes = await audio.read()
    question = meshapi_client.transcribe(audio_bytes, filename=audio.filename or "recording.webm")
    if not question.strip():
        raise HTTPException(400, "Could not make out any speech in that recording -- try again.")
    # 2. Moderate the transcribed question.
    _reject_if_flagged(question)

    # 3. Retrieve + generate the answer, then 4. always read it back as audio.
    answer_text, sources = rag.answer(question)
    audio_b64 = meshapi_client.synthesize_base64(answer_text)
    # Echo the transcribed question back so the UI can show what it heard.
    return VoiceAskResponse(question=question, answer=answer_text, sources=sources, audio_base64=audio_b64)
