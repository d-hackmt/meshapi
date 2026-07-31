"""Build order: 01/09 -- start here.

Application configuration for the MeshAPI-native RAG app.

All tunable values live here and are read from environment variables (loaded from
a local ``.env`` file via python-dotenv) so nothing sensitive is hard-coded. The
single most important value is ``MESH_API_KEY`` -- one MeshAPI key powers chat,
the managed RAG store, moderation, speech-to-text and text-to-speech, so there is
no vector-DB / embeddings / speech configuration to manage separately.
"""

import os

from dotenv import load_dotenv

# Read key=value pairs from a .env file in the project root into os.environ.
# Called at import time so every os.getenv() below sees them.
load_dotenv()


class Settings:
    # --- MeshAPI gateway ---------------------------------------------------
    # Base URL of the gateway; override only if you're pointed at a different
    # MeshAPI deployment.
    meshapi_base_url: str = os.getenv("MESHAPI_BASE_URL", "https://api.meshapi.ai")
    # The one API key that authenticates every MeshAPI call. We accept either
    # env var name (MESH_API_KEY is what .env.example uses) and default to "" so
    # validate() can raise a clear error instead of the SDK failing cryptically.
    meshapi_token: str = os.getenv("MESH_API_KEY") or os.getenv("MESHAPI_TOKEN") or ""
    # Which provider/model answers the questions. The "provider/model" string is
    # how MeshAPI routes to a specific backend (swap freely, e.g. mistral/...).
    meshapi_chat_model: str = os.getenv("MESHAPI_CHAT_MODEL", "openai/gpt-4o-mini")

    # --- RAG ---------------------------------------------------------------
    # No vector DB config here on purpose: MeshAPI's /v1/files store handles
    # chunking, embedding and storage server-side. We only choose how many
    # chunks to retrieve per question.
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "3"))

    # --- Voice in / out ----------------------------------------------------
    # Text-to-speech model + voice used to read answers back to the user.
    tts_model: str = os.getenv("MESHAPI_TTS_MODEL", "hexgrad/kokoro-82m")
    tts_voice: str = os.getenv("MESHAPI_TTS_VOICE", "af_heart")
    # Speech-to-text model used to transcribe a recorded question.
    stt_model: str = os.getenv("MESHAPI_STT_MODEL", "elevenlabs/scribe_v1")

    def validate(self) -> None:
        """Fail fast at startup if the one required credential is missing.

        Called from the FastAPI startup event so misconfiguration surfaces
        immediately with a readable message rather than deep inside an API call.
        """
        if not self.meshapi_token:
            raise RuntimeError("Missing required environment variable: MESH_API_KEY")


# Module-level singleton imported everywhere as `from .config import settings`.
settings = Settings()
