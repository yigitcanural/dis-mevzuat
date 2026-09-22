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
    environment: str = "development"
    public_base_url: str | None = None
    max_request_bytes: int = 1_048_576
    rate_limit_per_minute: int = 60
    tool_timeout: float = 20.0
    log_retention_days: int = 0
    openai_challenge_token: str | None = None
    allowed_hosts: tuple[str, ...] = ()
    source_allowed_domains: tuple[str, ...] = (
        "resmigazete.gov.tr",
        "saglik.gov.tr",
        "kvkk.gov.tr",
        "ushas.com.tr",
        "healthturkiye.com",
        "ticaret.gov.tr",
        "tdb.org.tr",
    )

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
            environment=os.getenv("DM_ENVIRONMENT", "development"),
            public_base_url=(os.getenv("DM_PUBLIC_BASE_URL") or "").rstrip("/") or None,
            max_request_bytes=int(os.getenv("DM_MAX_REQUEST_BYTES", "1048576")),
            rate_limit_per_minute=int(os.getenv("DM_RATE_LIMIT_PER_MINUTE", "60")),
            tool_timeout=float(os.getenv("DM_TOOL_TIMEOUT", "20")),
            log_retention_days=int(os.getenv("DM_LOG_RETENTION_DAYS", "0")),
            openai_challenge_token=os.getenv("OPENAI_APPS_CHALLENGE_TOKEN") or None,
            allowed_hosts=tuple(
                item.strip()
                for item in os.getenv("DM_ALLOWED_HOSTS", "").split(",")
                if item.strip()
            ),
            source_allowed_domains=tuple(
                item.strip().lower()
                for item in os.getenv(
                    "DM_SOURCE_ALLOWED_DOMAINS",
                    "resmigazete.gov.tr,saglik.gov.tr,kvkk.gov.tr,ushas.com.tr,"
                    "healthturkiye.com,ticaret.gov.tr,tdb.org.tr",
                ).split(",")
                if item.strip()
            ),
        )
