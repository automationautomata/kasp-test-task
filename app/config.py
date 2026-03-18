from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

WorkersType = Literal["processes", "threads"]


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_dsn: str
    lemmas_cache_maxsize: int = 10000
    writer_chunk_size_kb: int = 8
    max_workers: int = 4
    upload_chunk_size_mb: int = 1
    max_uploading_users: int = 10
    workers_type: WorkersType = "processes"
    save_batch_size: int = 200
    file_uploading_limit_gb: int | None = None
