from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    realtor_chat_id: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/realtor_bot.db"

    web_host: str = "0.0.0.0"
    web_port: int = 8000
    web_secret_key: str = "change-me-in-production"
    web_admin_username: str = "admin"
    web_admin_password: str = "change-me"

    rieltor_ua_max_price_usd: int = 100_000
    rieltor_ua_allowed_cities: str = "Киев,Львов"
    rieltor_ua_base_url: str = "https://rieltor.ua"
    rieltor_ua_request_timeout: int = 10

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Managed Postgres providers (Railway included) hand out a plain
        `postgres://`/`postgresql://` URL — SQLAlchemy's async engine needs
        the `+asyncpg` driver spelled out explicitly."""

        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value[len("postgres://") :]
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value

    @property
    def rieltor_ua_allowed_cities_list(self) -> list[str]:
        return [c.strip() for c in self.rieltor_ua_allowed_cities.split(",") if c.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
