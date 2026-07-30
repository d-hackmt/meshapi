import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # MeshAPI gateway
    meshapi_base_url: str = os.getenv("MESHAPI_BASE_URL", "https://api.meshapi.ai")
    meshapi_token: str = os.getenv("MESH_API_KEY") or os.getenv("MESHAPI_TOKEN") or ""
    meshapi_chat_model: str = os.getenv("MESHAPI_CHAT_MODEL", "openai/gpt-4o-mini")
    meshapi_embedding_model: str = os.getenv("MESHAPI_EMBEDDING_MODEL", "openai/text-embedding-3-small")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

    # Pinecone
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "meshapi-demo-kb")
    pinecone_cloud: str = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")

    # RAG
    top_k: int = int(os.getenv("RAG_TOP_K", "3"))

    def validate(self) -> None:
        missing = [
            name
            for name, value in [
                ("MESH_API_KEY", self.meshapi_token),
                ("PINECONE_API_KEY", self.pinecone_api_key),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required environment variable(s): " + ", ".join(missing)
            )


settings = Settings()
