# meshapi

Teaching demos for the [MeshAPI](https://developers.meshapi.ai) AI model gateway — one API key, one
OpenAI-shaped API, many LLM providers behind it.

## Contents

- **`01_meshapi_basics.ipynb`** — gateway fundamentals: client setup, live model discovery, chat
  completions across two providers (OpenAI, Mistral by default — easily swapped), streaming, and the
  `compare` endpoint.
- **`02_rag_multiagent.ipynb`** — a RAG + multi-agent capstone: MeshAPI's own embeddings endpoint +
  Pinecone for retrieval, and a Researcher → Writer → Critic pipeline built with LangChain's
  `create_agent`, each agent routed through a different provider via the MeshAPI gateway.
- **`app/`** — the same simple RAG pipeline as a modular FastAPI backend with a Jinja-templated
  HTML frontend (no notebook required). Retrieval is self-managed: we chunk, embed, and query a
  Pinecone index ourselves.
- **`native_rag_app/`** — the same demo again, but retrieval is entirely MeshAPI's managed RAG
  service (`/v1/files` upload + search) instead of Pinecone — no chunking code, no vector DB. It also
  adds voice: speak your question (speech-to-text) and hear the answer read back (text-to-speech).
  See [Comparing the two RAG apps](#comparing-the-two-rag-apps) below.
- **`features.ipynb`** / **`features_lazy_imports.ipynb`** — the full feature-tour notebook, in two
  import styles. `features.ipynb` imports everything up front in one setup cell; the `_lazy_imports`
  copy imports each SDK class right where it's first used, section by section, so any single section
  is readable on its own without scrolling back to cell 3. Same cells, same live outputs otherwise.
- **`cli_and_claude_code.md`** — how to use `meshapi-code` (MeshAPI's own terminal coding agent,
  `uv tool install meshapi-code`) and how to add MeshAPI as an MCP tool inside Claude Code itself —
  two separate, unrelated integrations, both covered with verified install/config details.
- **`mcp_capabilities.md`** — `meshapi-code` vs the MCP server compared side by side (a whole separate
  agent vs. extra tools for Claude Code), what MCP can and can't do (no audio/video/batch — verified
  live), and real generate-image/video/TTS examples run through each.

## FastAPI RAG app

```
app/
  config.py          settings loaded from environment variables
  vectorstore.py       Pinecone index setup + query
  data.py               sample knowledge base + chunking
  meshapi_client.py   MeshAPI gateway client (chat completions, embeddings)
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
- A MeshAPI key (`MESH_API_KEY`) from the [MeshAPI dashboard](https://developers.meshapi.ai) — used for both chat and embeddings
- A Pinecone key (`PINECONE_API_KEY`) from [pinecone.io](https://www.pinecone.io)

## Native RAG app (`native_rag_app/`)

Same idea, retrieval rebuilt on MeshAPI's own managed RAG service instead of Pinecone, plus voice
input/output:

```
native_rag_app/
  config.py          settings loaded from environment variables
  data.py               sample knowledge base (no chunking code -- MeshAPI chunks server-side)
  meshapi_client.py   MeshAPI gateway client (chat, RAG upload/search, TTS, STT)
  rag.py                 ingest / retrieve / answer orchestration
  schemas.py           request/response models
  main.py               FastAPI routes, incl. voice endpoints
  templates/index.html   single-page UI: type or 🎤 speak a question, hear the answer read back
  static/app.js           mic recording (MediaRecorder) + fetch calls to the JSON API
  static/style.css
```

### Setup & run

Uses the same `.env` / `requirements.txt` as `app/` — no Pinecone key needed for this one. Only
addition: `python-multipart` is already in `requirements.txt` (needed for the voice upload endpoint).

```bash
uvicorn native_rag_app.main:app --reload
```

Open `http://127.0.0.1:8000`, click **"Index knowledge base"** once, then type a question or click
🎤 and ask out loud. Or hit the JSON API directly:

```bash
curl -X POST http://127.0.0.1:8000/api/ingest
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What happens if I go over my storage limit?", "speak": true}'
```

`speak: true` (or any `/api/ask-voice` call) returns a base64 mp3 in `audio_base64` alongside the
text answer.

## Comparing the two RAG apps

| | `app/` (Pinecone) | `native_rag_app/` (MeshAPI RAG) |
|---|---|---|
| Chunking | Ours (`data.chunk_text`, fixed char window + overlap) | MeshAPI's, automatic on upload — we don't control the strategy |
| Embedding | Explicit `meshapi_client.embed()` call we wire into the ingest step | Implicit — happens server-side after `upload_file(embed=True)` |
| Storage | Our own Pinecone index (`PINECONE_INDEX_NAME`), scoped to us by construction | One shared store per MeshAPI API key — see gotcha below |
| Retrieval code | `vectorstore.py` (a whole module: index create/upsert/query) | One `client.rag.search(...)` call, no separate module |
| Extra infra/credentials | Needs a Pinecone account + API key | None — same MeshAPI key does everything |
| Voice in/out | Not built | Built — STT question in, TTS answer out |

**The one real gotcha we hit building the MeshAPI-native version:** `/v1/files` has no delete
endpoint (confirmed live — `DELETE /v1/files/{id}` returns `405 Method Not Allowed`), and uploads
aren't scoped to an "index" the way Pinecone's are — every file ever uploaded with a given API key
lands in the same account-wide searchable pool, forever. Re-running ingest, or just having used the
same key for other testing, means `client.rag.search(...)` can return stale or unrelated documents
mixed in with yours. The fix `native_rag_app/rag.py` uses: track the `file_id`s from your own
`ingest()` call in a small local state file and always pass them to `SearchRequest(..., file_ids=...)`
to scope search to just your own data. (`SearchRequest` also has a `filter` param for metadata
filtering, but it errored server-side in testing — `file_ids` is the reliable option.)

**Bottom line:** the MeshAPI-native app is meaningfully less code and needs one less service
(Pinecone) — but you trade away control over chunking strategy and inherit the shared-store gotcha
above. Pinecone remains the better choice if you need your own chunking logic, multiple isolated
indexes, or guaranteed deletion.
