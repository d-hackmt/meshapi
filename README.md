# meshapi

Teaching demos for the [MeshAPI](https://developers.meshapi.ai) AI model gateway — one API key, one
OpenAI-shaped API, many LLM providers behind it.

## Contents

- **`01_meshapi_basics.ipynb`** — gateway fundamentals: client setup, live model discovery, chat
  completions across two providers (OpenAI, Mistral by default — easily swapped), streaming, and the
  `compare` endpoint.
- **`02_rag_multiagent.ipynb`** — a RAG + multi-agent capstone: Jina embeddings + Pinecone for
  retrieval, and a Researcher → Writer → Critic pipeline built with LangChain's `create_agent`,
  each agent routed through a different provider via the MeshAPI gateway.
- **`app/`** — the same simple RAG pipeline as a modular FastAPI backend with a Jinja-templated
  HTML frontend (no notebook required).

## FastAPI RAG app

```
app/
  config.py          settings loaded from environment variables
  embeddings.py       Jina embeddings client
  vectorstore.py       Pinecone index setup + query
  data.py               sample knowledge base + chunking
  meshapi_client.py   MeshAPI gateway client (chat completions, model discovery)
  rag.py                 ingest / retrieve / answer orchestration
  schemas.py           request/response models
  main.py               FastAPI routes
templates/index.html   Jinja UI (question form, answer, sources)
static/style.css
```

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env      # then fill in your keys
```

### Run

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`, then index the sample knowledge base once:

```bash
curl -X POST http://127.0.0.1:8000/api/ingest
```

After that, ask questions from the web UI, or hit the JSON API directly:

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What happens if I go over my storage limit?"}'
```

### Environment variables

See `.env.example` for the full list. You'll need:
- A MeshAPI key (`MESH_API_KEY`) from the [MeshAPI dashboard](https://developers.meshapi.ai)
- A Jina AI key (`JINA_API_KEY`) from [jina.ai](https://jina.ai)
- A Pinecone key (`PINECONE_API_KEY`) from [pinecone.io](https://www.pinecone.io)
