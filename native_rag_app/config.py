import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # MeshAPI gateway
    meshapi_base_url: str = os.getenv("MESHAPI_BASE_URL", "https://api.meshapi.ai")
    meshapi_token: str = os.getenv("MESH_API_KEY") or os.getenv("MESHAPI_TOKEN") or ""
    meshapi_chat_model: str = os.getenv("MESHAPI_CHAT_MODEL", "openai/gpt-4o-mini")

    # RAG -- no vector DB config here, MeshAPI's /v1/files store handles it
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "3"))

    # Voice in/out
    tts_model: str = os.getenv("MESHAPI_TTS_MODEL", "hexgrad/kokoro-82m")
    tts_voice: str = os.getenv("MESHAPI_TTS_VOICE", "af_heart")
    stt_model: str = os.getenv("MESHAPI_STT_MODEL", "elevenlabs/scribe_v1")

    def validate(self) -> None:
        if not self.meshapi_token:
            raise RuntimeError("Missing required environment variable: MESH_API_KEY")


settings = Settings()
