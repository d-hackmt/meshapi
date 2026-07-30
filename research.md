# MeshAPI Feature Research

A plain-language inventory of everything MeshAPI offers, checked against the official docs
(`developers.meshapi.ai`) **and** verified live against a real API key where possible — not just
copied from the docs. Goal: know exactly what's available, and exactly how much of it our
notebooks/app actually use so far.

---

## 1. What is MeshAPI, in one picture

Think of MeshAPI as a **universal power adapter** for AI models. Normally, if you want to use
OpenAI, Anthropic, Mistral, and 100+ other providers, you'd need a different account, a different
API key, and slightly different code for each one. MeshAPI sits in the middle: **one key, one API
shape, 997 models across 124 providers** behind it.

```mermaid
flowchart LR
    App["Your App\n(notebook / FastAPI / CLI)"] -->|"one rsk_... key"| Gateway["MeshAPI Gateway"]
    Gateway --> P1["OpenAI"]
    Gateway --> P2["Anthropic"]
    Gateway --> P3["Mistral"]
    Gateway --> P4["Google / Vertex"]
    Gateway --> P5["Amazon Bedrock"]
    Gateway --> P6["DeepSeek, Cohere,\nElevenLabs, ...121 more"]

    Gateway -.tracks.-> Bill["Billing / spend caps"]
    Gateway -.applies.-> Fallback["Auto retry + fallback\nif a provider is down"]
    Gateway -.optional.-> Cache["Response cache\n(free, 24h)"]
```

Everything below is a **capability of that one gateway box** — different doors on the same building.

---

## 2. Scorecard — how much have we actually used?

```mermaid
pie showData
    title Features used vs not used (32 total)
    "Used" : 9
    "Passive / automatic (not configured by us)" : 2
    "Not used yet" : 21
```

**We've used 9 out of 32 individually countable features so far** — the core "talk to an LLM" path
(chat, streaming, tool calling, structured outputs, compare, model discovery, error handling, the
Python SDK itself) **plus embeddings**, which we originally did through Jina and have since switched
to MeshAPI's own `/v1/embeddings`. Two more (automatic retry/fallback and response caching) benefit
us passively without us configuring anything. Everything else — MeshAPI's built-in RAG/file-search,
images, video, audio, moderations, memory/guardrails, batch, prompt templates, auto-router,
usage/billing APIs — is still untouched. That's normal for a first pass; this doc is the checklist
for what a "feature tour" notebook could cover next.

---

## 3. The full feature list

### 3.1 Talking to models (the part we've used)

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| Chat Completions | Send messages, get a reply. The basic building block. | `POST /v1/chat/completions` | ✅ |
| Streaming | Get the reply word-by-word as it's generated, instead of waiting for the whole thing. | same endpoint, `stream: true` | ✅ |
| Tool / Function calling | Let the model call your Python functions (search a DB, check weather, etc). | `tools` / `tool_choice` params | ✅ |
| Structured outputs | Force the model to reply in a JSON shape you define (via a Pydantic model), instead of free text. | `response_format` param | ✅ |
| Compare | Ask 2-10 models the same question at once, side by side, with an optional AI-written summary of the differences. | `POST /v1/chat/compare` | ✅ |
| Model discovery | Ask the gateway "what models do you actually have right now" instead of guessing model names. | `GET /v1/models` (+ `/free`, `/paid`, `/search`) | ✅ |
| Error handling | Structured error objects (`status`, `error_code`, `retry_after_seconds`) instead of raw text errors. | n/a (SDK feature) | ✅ |
| **Responses API** | A newer, alternative chat-style endpoint built for reasoning models (o1-style), background/async jobs, and built-in tools (web search, code interpreter). We used plain Chat Completions instead. | `POST /v1/responses` | ❌ |
| **Auto Router** | Set `model: "auto"` and MeshAPI's own classifier model picks the best/cheapest model for your prompt automatically. | any endpoint, `model="auto"` | ❌ |

### 3.2 Retrieval & memory (RAG)

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| **File upload + built-in RAG** | Upload a PDF/doc, MeshAPI chunks + embeds + stores it for you, then you can search it. A full RAG pipeline as a service. | `POST /v1/files`, `/v1/files/search` | ❌ — we still store/query vectors in Pinecone ourselves instead of using this end-to-end managed version |
| **Embeddings API** | Turn text into vectors (numbers) for search/similarity — **44 embedding models across 12 brands** are available (OpenAI, Cohere, Amazon Titan, Mistral, Google, Qwen, BAAI, and more), all through the same gateway. | `POST /v1/embeddings` | ✅ — switched from Jina to `openai/text-embedding-3-small` via MeshAPI (`dimensions=1024`, same trick Jina used to control vector size) |
| **Memory** | Durable per-user "sticky notes" attached to every chat call via a header. Three flavors: `guardrail` (a rule that must ALWAYS be included, e.g. "never give financial advice"), `preference` (style hints, included if there's room), `fact` (relevant facts, ranked by relevance). | `POST /v1/memories`, header `x-mem-id: ...` | ❌ |

> **About "guardrails" specifically** (you asked about this): there is **no separate "Guardrails"
> product** in MeshAPI. What they call a guardrail is just one of the three Memory item types above
> — a rule you store once that gets injected into every future request, and is never silently
> dropped even if the request is long. It is **not** a content-safety / jailbreak-detection system.
> That job is done by the separate **Moderations** endpoint below.

### 3.3 Other content types

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| Image generation | Text prompt → generated image. | `POST /v1/images/generations` | ❌ |
| Image editing | Inpaint, outpaint, remove background, upscale, mix two images, etc. | `POST /v1/images/edits` | ❌ |
| Video generation | Text/image prompt → generated video clip (async — you poll for it). | `POST /v1/video/generations` | ❌ |
| Text-to-speech | Text → spoken audio. | `POST /v1/audio/speech` | ❌ |
| Speech-to-text | Audio → text transcript (supports speaker labeling). | `POST /v1/audio/transcriptions` | ❌ |
| Audio translation | Audio in one language → transcript/translation in another. | `POST /v1/audio/translations` | ❌ |
| Realtime speech-to-speech | Live two-way voice conversation over a WebSocket (like a phone call with an AI). | `WS /v1/realtime` | ❌ |

### 3.4 Safety & moderation

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| Moderations | Checks text/images for 13 categories of unsafe content (harassment, hate, violence, self-harm, sexual, etc.) and gives each a flag + confidence score. **We tested this live** — see below. | `POST /v1/moderations` | ❌ (verified it works, just not wired into our app) |

Live test result (using the account's real key, not from docs) — sending `"I want to hurt someone"`
correctly flagged `violence: true` with a 0.87 confidence score, and returned all 13 categories:
`harassment`, `harassment/threatening`, `sexual`, `hate`, `hate/threatening`, `illicit`,
`illicit/violent`, `self-harm/intent`, `self-harm/instructions`, `self-harm`, `sexual/minors`,
`violence`, `violence/graphic`. One documentation gap we found: **pricing for this endpoint isn't
published anywhere** in the docs.

### 3.5 Reliability & cost (mostly automatic)

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| Automatic retry & fallback | If a provider is slow/down, MeshAPI retries, then tries a different provider, then a similar model — automatically, no code needed. | n/a — always on | 🟡 passive (benefits us, but we never triggered or configured it) |
| Response caching | Identical requests (temperature 0, no tools) are cached free for 24h — repeat questions cost nothing. | header `X-Mesh-Cache`, param `cache` | 🟡 passive (our temperature > 0 calls mostly wouldn't qualify anyway) |
| Batch API | Submit hundreds of requests as one job, cheaper, processed within a time window (e.g. 24h) instead of real-time. | `POST /v1/batches` | ❌ |

### 3.6 Prompts & workflow helpers

| Feature | In plain words | Endpoint | Used by us? |
|---|---|---|:---:|
| Prompt Templates | Save a reusable system prompt with `{{variables}}` on the server, so your app just says "use template X" instead of re-sending the whole prompt every time. | `/v1/templates` (CRUD) | ❌ |
| Web Search | Built-in web search tool (own engine, falls back to Tavily), returns an AI-written answer + sources. | `POST /v1/web/search` | ❌ |

### 3.7 Accounts, billing & ops (dashboard / raw HTTP — not in the Python SDK)

These exist and we confirmed the Python SDK **does not** wrap them — the installed `MeshAPI`
client only exposes: `chat, responses, embeddings, compare, batches, models, templates, images,
videos, audio, rag, moderations, web, router, realtime`. Anything below needs a raw HTTP call or
the dashboard.

| Feature | In plain words | Used by us? |
|---|---|:---:|
| API key management | Create/limit/suspend `rsk_...` keys, set per-key spend caps and rate limits. | ❌ (did it manually in the dashboard) |
| Usage & balance | Check how much you've spent, remaining balance, per-model breakdown, live rate-limit status. | ❌ |
| Organizations & Teams | Company accounts with shared billing, roles (Owner/Admin/Member), and spend limits that cascade org → team → member → key (smallest limit wins). | ❌ |
| BYOK (Bring Your Own Key) | Use your own OpenAI/Bedrock/Vertex account credentials through MeshAPI instead of their shared pool. | ❌ |

### 3.8 Developer tooling

| Feature | In plain words | Used by us? |
|---|---|:---:|
| Python SDK | The `meshapi` package — what all our notebooks/app are built on. | ✅ |
| Go SDK | Same idea, for Go projects. | n/a (not our language) |
| MCP Server | Lets AI coding tools (Claude Code, Cursor, Claude Desktop) call MeshAPI directly as a tool — e.g. "list models," "check balance" from inside your editor's chat. | ❌ |
| CLI (`meshapi-code`) | A separate terminal app — chat with any model and have it read/write files and run commands in your project, similar to Claude Code. Not a library you import. | ❌ |

---

## 4. Where LangChain fits in

One thing worth being precise about: LangChain's `create_agent` is **not a MeshAPI feature** — it's
a separate framework we chose to use for the multi-agent notebook. MeshAPI just needs to look like
an OpenAI-compatible endpoint for LangChain to talk to it (`ChatOpenAI(base_url=..., api_key=...)`).
So "tool calling" and "structured output" in the table above are true MeshAPI/model capabilities;
`create_agent` is the framework we used to orchestrate them.

---

## 5. Everything we have **not** tried yet (candidates for a "feature tour" notebook)

In rough order of "most useful to show a class":

1. **MeshAPI's fully managed RAG** (`/v1/files`, `/v1/files/search`) — we already use its embeddings
   endpoint; this would replace our own Pinecone chunk/embed/upsert/query code entirely and show
   the "gateway does the whole RAG pipeline too" contrast.
2. **Moderations** — one API call, very visual, easy "why does this matter" story.
3. **Auto Router** (`model: "auto"`) — neat "let the gateway pick" demo.
4. **Prompt Templates** — shows the "server-managed prompts" production pattern.
5. **Images** (generation + editing) — high visual payoff for a demo.
6. **Memory / guardrails** — directly answers "how do I make the model always follow a rule."
7. **Text-to-speech / speech-to-text** — fun, tangible, easy to demo live.
8. **Usage & balance API** — "how much did this notebook just cost me" is a great teaching moment.
9. **Batch API, Video, Realtime audio, BYOK, Orgs/Teams** — more advanced/niche, good for a mention
   rather than a full demo.

---

## 6. Documentation gaps we found (for transparency)

- Moderations endpoint pricing is not published anywhere in the docs.
- The full list of embedding models/providers isn't shown in the docs page itself — we only got the
  complete list (44 models, 12 brands) by querying the live `/v1/models` catalog directly.
- There is no dedicated "Guardrails" doc page — it's a sub-feature of Memory, which could confuse
  anyone searching for "guardrails" expecting a content-safety product.

---

## 7. Sources

- `developers.meshapi.ai` — full doc site, crawled via its `llms.txt` index (Introduction, Guides,
  API Reference, Python/Go SDK docs, Infrastructure, Agents/MCP, CLI, Debugging sections)
- Live verification against our real MeshAPI key: `client.models.list()` (997 models / 124 brands /
  44 embedding models), `client.moderations.create(...)` (full 13-category response), and
  `dir(MeshAPI(...))` (confirms which resources the Python SDK actually wraps)
