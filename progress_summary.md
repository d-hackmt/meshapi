# Progress Summary

Changes made since the last commit (`6c6827a — Fix TemplateResponse crash on modern Starlette`).

## 1. New: `native_rag_app/` — MeshAPI-native RAG app with voice

A second FastAPI RAG app, sibling to `app/`, built to answer the question "how much of `app/`'s
Pinecone plumbing does MeshAPI's own RAG service replace?"

- Retrieval uses MeshAPI's managed RAG (`client.rag.upload_file` + `client.rag.search`) instead of
  Pinecone — no chunking code, no vector DB, no separate embeddings step to wire up ourselves.
- Adds voice: click the mic, ask out loud, and the app transcribes it (speech-to-text,
  `elevenlabs/scribe_v1`), runs the same retrieve → answer pipeline, and speaks the answer back
  (text-to-speech, `hexgrad/kokoro-82m`).
- Files: `config.py`, `data.py`, `meshapi_client.py`, `rag.py`, `schemas.py`, `main.py`,
  `templates/index.html`, `static/app.js`, `static/style.css`.
- Tested live end-to-end against a real MeshAPI key: ingest, typed questions, and a real recorded
  voice question (speech in → correct transcription → correct answer → playable spoken reply).

**Bug found and fixed while building it:** MeshAPI's `/v1/files` RAG store is account-wide with no
per-app scoping and **no delete endpoint** (`DELETE /v1/files/{id}` → `405`) — every file ever
uploaded with a given API key stays searchable forever. An earlier test upload polluted real search
results before this was caught. Fix: `rag.py` tracks the `file_id`s from its own `ingest()` call in
a local, gitignored state file (`native_rag_app/.rag_state.json`) and always passes them to
`SearchRequest(file_ids=...)` so search is scoped to just this app's own data.

## 2. New: `features_lazy_imports.ipynb`

A copy of `features.ipynb` with SDK imports moved from one big up-front setup cell to the point of
first use in each section, so any single section reads standalone. Mechanical reorg only — no logic
or output changes. Verified by syntax-checking every cell and manually tracing import order rather
than re-running the whole notebook against the live API (that would re-incur the real image/video/
audio costs already spent testing `features.ipynb`).

## 3. `README.md`

- Documents `native_rag_app/` alongside `app/` and `features_lazy_imports.ipynb` alongside
  `features.ipynb` in the Contents list.
- Adds a "Native RAG app" section with its file layout, setup, and run instructions.
- Adds a "Comparing the two RAG apps" section: a side-by-side table (chunking control, credentials
  needed, voice support) plus the `/v1/files` gotcha above, with a recommendation that
  `native_rag_app` is the stronger pick for live demos (one credential instead of two, voice is a
  real wow-factor) while `app/`'s Pinecone approach is the more transferable lesson for general RAG
  architecture.

## 4. `.gitignore`

Added `native_rag_app/.rag_state.json` (the local file-id tracking state described above).

## 5. `requirements.txt`

Added `requests` as an explicit dependency.
