import base64
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import meshapi_client, rag
from .config import settings
from .schemas import AskRequest, AskResponse, IngestResponse, VoiceAskResponse

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="MeshAPI Native RAG Demo")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def on_startup() -> None:
    settings.validate()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/api/ingest", response_model=IngestResponse)
def api_ingest() -> IngestResponse:
    uploaded, ready = rag.ingest()
    return IngestResponse(documents_uploaded=uploaded, embedded_ready=ready)


@app.post("/api/ask", response_model=AskResponse)
def api_ask(req: AskRequest) -> AskResponse:
    answer_text, sources = rag.answer(req.question, top_k=req.top_k)
    audio_b64 = base64.b64encode(meshapi_client.synthesize(answer_text)).decode() if req.speak else None
    return AskResponse(answer=answer_text, sources=sources, audio_base64=audio_b64)


@app.post("/api/ask-voice", response_model=VoiceAskResponse)
async def api_ask_voice(audio: UploadFile = File(...)) -> VoiceAskResponse:
    audio_bytes = await audio.read()
    question = meshapi_client.transcribe(audio_bytes, filename=audio.filename or "recording.webm")
    if not question.strip():
        raise HTTPException(400, "Could not make out any speech in that recording -- try again.")

    answer_text, sources = rag.answer(question)
    audio_b64 = base64.b64encode(meshapi_client.synthesize(answer_text)).decode()
    return VoiceAskResponse(question=question, answer=answer_text, sources=sources, audio_base64=audio_b64)
