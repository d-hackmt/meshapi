from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import rag
from .config import settings
from .schemas import AskRequest, AskResponse, IngestResponse

app = FastAPI(title="MeshAPI RAG Demo")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup() -> None:
    settings.validate()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "question": "", "answer": None, "sources": []},
    )


@app.post("/", response_class=HTMLResponse)
def ask_form(request: Request, question: str = Form(...)) -> HTMLResponse:
    answer_text, sources = rag.answer(question)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "question": question, "answer": answer_text, "sources": sources},
    )


@app.post("/api/ingest", response_model=IngestResponse)
def api_ingest() -> IngestResponse:
    chunks_indexed = rag.ingest()
    return IngestResponse(chunks_indexed=chunks_indexed)


@app.post("/api/ask", response_model=AskResponse)
def api_ask(req: AskRequest) -> AskResponse:
    answer_text, sources = rag.answer(req.question, top_k=req.top_k)
    return AskResponse(answer=answer_text, sources=sources)
