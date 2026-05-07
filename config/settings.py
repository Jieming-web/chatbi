from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


_CONFIG_PATH = Path(__file__).parent / "settings.yaml"


class EmbeddingSettings(BaseModel):
    model_name: str = "all-MiniLM-L6-v2"


class RetrieverSettings(BaseModel):
    type: str = "dense"
    top_k: int = 10
    final_tables: int = 5


class RerankerSettings(BaseModel):
    type: str = "llm"
    top_k: int = 3
    model_name: Optional[str] = None


class LLMSettings(BaseModel):
    model: str = "gpt-4o"
    temperature: float = 0.0


class DBSettings(BaseModel):
    path: str = "data/Ecommerce.db"


class MCPSettings(BaseModel):
    port: int = 8787
    fallback_on_error: bool = True


class Settings(BaseModel):
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    retriever: RetrieverSettings = Field(default_factory=RetrieverSettings)
    reranker: RerankerSettings = Field(default_factory=RerankerSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    db: DBSettings = Field(default_factory=DBSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)


def _load() -> Settings:
    if not _CONFIG_PATH.exists():
        return Settings()
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return Settings(**raw)


settings = _load()
