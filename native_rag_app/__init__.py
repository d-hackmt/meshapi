"""MeshAPI-native RAG app package.

A self-contained FastAPI app that answers questions about a sample knowledge base
using MeshAPI end to end: the managed RAG store (upload + search) for retrieval,
chat completions for generation, moderation for input safety, and speech-to-text
/ text-to-speech for voice interaction -- all through one client and one API key.

Modules, in build order (each file's docstring/header comment repeats its number):
    01  config              environment-driven settings (the MeshAPI key, models, top_k)
    02  data                the sample knowledge base
    03  meshapi_client      thin wrapper around the MeshAPI SDK (chat/RAG/moderation/STT/TTS)
    04  rag                 ingest / retrieve / answer orchestration
    05  schemas             pydantic request/response models
    06  main                the FastAPI app and HTTP routes
    07  templates/index.html   the page
    08  static/app.js           frontend logic (mic, fetch calls, rendering)
    09  static/style.css         styling, last

Run with:  uvicorn native_rag_app.main:app --reload
"""
