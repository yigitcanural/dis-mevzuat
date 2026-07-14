from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    enable_admin_tools: bool
    max_source_bytes: int
    request_timeout: float
    embedding_api_key: str | None
    embedding_api_base: str
    embedding_model: str
    transport: str
    host: str
    port: int

    @property
    def db_path(self) -> Path:
        return self.data_dir / "dis_mevzuat.sqlite3"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        data_dir = Path(os.getenv("DM_DATA_DIR", "./data")).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "raw").mkdir(exist_ok=True)
        (data_dir / "staging").mkdir(exist_ok=True)
        return cls(
            data_dir=data_dir,
            # Güvenli varsayılan: public bir sunucuda kaynak değiştirme araçları
            # açıkça izin verilmedikçe yayınlanmaz.
            enable_admin_tools=_bool_env("DM_ENABLE_ADMIN_TOOLS", False),
            max_source_bytes=int(os.getenv("DM_MAX_SOURCE_BYTES", "15000000")),
            request_timeout=float(os.getenv("DM_REQUEST_TIMEOUT", "30")),
            embedding_api_key=os.getenv("DM_EMBEDDING_API_KEY") or None,
            embedding_api_base=os.getenv(
                "DM_EMBEDDING_API_BASE", "https://openrouter.ai/api/v1"
            ).rstrip("/"),
            embedding_model=os.getenv(
                "DM_EMBEDDING_MODEL", "openai/text-embedding-3-small"
            ),
            transport=os.getenv("DM_TRANSPORT", "stdio"),
            host=os.getenv("DM_HOST", "127.0.0.1"),
            port=int(os.getenv("DM_PORT", "8000")),
        )
