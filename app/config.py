from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Clinical Biomechanics Engine"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    web_dist_dir: Path = Path("dist")
    
    # Tambahkan atribut ini agar sesuai dengan isi file .env Anda
    port: int = 8000
    groq_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()