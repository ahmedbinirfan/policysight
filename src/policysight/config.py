from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    support_floor: float = 0.15
    port: int = 8000
    # Repo root = parents[2] from src/policysight/config.py
    root: Path = Path(__file__).resolve().parents[2]
    corpus_dir: Path = root / "data" / "corpus"
    golden_path: Path = root / "data" / "golden" / "qa.json"
    index_dir: Path = root / "data" / "index"


settings = Settings()
