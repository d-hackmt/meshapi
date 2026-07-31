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

---

## 6. Content moderation added to `native_rag_app/`

Neither RAG app had any input filtering — a question went straight from the request into the
RAG/LLM pipeline. Added `meshapi_client.is_flagged()` (`client.moderations.create`), checked on both
`/api/ask` and `/api/ask-voice` before retrieval or generation runs, so flagged input never reaches
the LLM (and never costs anything either, since it's rejected first). Tested live: a normal question
still answers correctly with sources; an unsafe one now gets `HTTP 400` with a clear message.
`app.js` also updated to surface that message in the UI instead of a generic "something went wrong."

## 7. MeshAPI as an MCP tool inside Claude Code

- `.mcp.json` (gitignored, holds a real key) set up so Claude Code (the VS Code extension, no
  separate `claude` CLI needed) auto-loads the `mesh-api` MCP server on window reload. Verified live
  by calling `get_balance` through the tool and getting a real balance back.
- `.mcp.json.example` (committed, placeholder key) added so others can `copy .mcp.json.example
  .mcp.json` and drop in their own key.
- Used the MCP tools live to generate a real image (`generate_image`, `openai/gpt-image-1`). Video
  generation and TTS turned out to have **no MCP tool at all** — dropped to the Python SDK directly
  for those (video: `byteplus/seedance-1-0-pro-fast`, ~40s for a 3s clip; audio: `sarvam/bulbul:v2`
  for Hindi/Hinglish, `elevenlabs/eleven_flash_v2_5` for natural English).
- Two quirks found doing this: `generate_image` always returns inline base64 regardless of
  `response_format`, and the actual audio format returned doesn't always match what you'd guess from
  the model name (check magic bytes — Sarvam returns WAV, ElevenLabs returns MP3).

## 8. Repo reorganized: `docs/`, `experiments/`, `outputs/`

- All standalone `.md` docs moved into `docs/`, renumbered `01`–`07`, with `docs/README.md` as the
  ordered index.
- All notebooks moved into `experiments/`.
- All generated demo media moved into `outputs/{img,audio,video}/`.
- Root `README.md` rewritten around `native_rag_app/` as the primary demo.

**Note:** `01_meshapi_basics.ipynb`, `02_rag_multiagent.ipynb`, and `features_lazy_imports.ipynb`
all made it into `experiments/` intact. **`features.ipynb` (the original, fully-executed ~3.9MB
notebook) did not** — it's absent from `experiments/` and wasn't found anywhere else on disk when
checked. It's not lost forever (still recoverable from git history, e.g. `git show
<earlier-commit>:features.ipynb`), but flagging this explicitly since it wasn't an intentional
deletion as far as this summary can tell.

## 9. `app/` (the Pinecone RAG app) deleted entirely

Now that `native_rag_app/` fully replaces it: removed `app/` (all 8 files) and its root-level
`static/`/`templates/` (which were `app/`'s frontend, never shared with `native_rag_app/`, which has
its own). Cleaned up the dead config left behind — `pinecone` dropped from `requirements.txt`;
`PINECONE_*`, `MESHAPI_EMBEDDING_MODEL`, and `EMBEDDING_DIMENSIONS` dropped from `.env.example` (none
of them were ever read by `native_rag_app/config.py`). Verified `native_rag_app` still imports and
runs cleanly with no stray references to the deleted module.

## 10. Full `docs/` review

Read and verified every file in `docs/` end to end. Real issues found and fixed:
- `docs/01_research.md`'s scorecard was stale — File-upload+RAG and Moderations are now genuinely
  used (in `native_rag_app/`), not just demoed; flipped both to ✅ and recounted (9→11 used).
- `docs/03_cli_and_claude_code.md`'s PATH guidance was a single mixed paragraph; restructured into an
  explicit local-vs-global split with a diagram (a `cmd.exe` window opened *before* `uv tool
  update-shell` runs keeps its stale PATH — the actual thing that caused confusion).
- `docs/04_mcp_capabilities.md` had two broken relative links left over from pre-reorg filenames.
- `docs/05_meshapi_vs_claude_code.md` claimed Claude Code is a separate desktop GUI application —
  false, it's a CLI/terminal tool (this VS Code extension included), same shape as `meshapi-code`.
  Rewritten with corrected facts, 3 diagrams, and less overlap with doc 04.
- Added small flow diagrams to every doc that lacked one, including the root `README.md` and
  `docs/README.md` itself.
- `docs/06_native_rag_app.md` (then `07`, since renumbered) gained a section on what chunks/embeds/stores the documents — checked
  MeshAPI's official docs directly and confirmed the chunking strategy, internal embedding model, and
  vector database are all undisclosed (a genuine black box), documenting what *is* observable instead
  (`chunk_index` on results, `total_tokens` billed per file).

## 11. Build-order numbering added to `native_rag_app/`

For live-coding demos: every file's docstring/header comment now starts with `Build order: 0X/09`
(no files renamed), following the actual dependency chain — `config` → `data` → `meshapi_client` →
`rag` → `schemas` → `main` → `templates/index.html` → `static/app.js` → `static/style.css`.
`__init__.py`'s existing module list extended with the same numbers plus the 3 frontend files it was
missing.
