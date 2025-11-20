# backend/src/app/config.py
from __future__ import annotations

from typing import List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    app_title: str = Field("SeatCheck API", alias="APP_TITLE")
    app_version: str = Field("0.1.0", alias="APP_VERSION")
    debug: bool = Field(True, alias="DEBUG")

    app_base: str = Field("http://localhost:8081", alias="APP_BASE")
    cas_base: str = Field("https://secure.its.yale.edu/cas", alias="CAS_BASE")
    session_secret: str = Field("dev-insecure-change-me", alias="SESSION_SECRET")
    dev_auth: bool = Field(True, alias="DEV_AUTH")

    database_url: str = Field("postgresql://localhost/seatcheck", alias="DATABASE_URL")
    database_echo: bool = Field(False, alias="DATABASE_ECHO")

    # NOTE: changed alias to avoid collision with allowed_origins (list field)
    allowed_origins_raw: str = Field("*", alias="CORS_ALLOWED_ORIGINS")
    allowed_origins: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env that aren't in Settings class
    )

    @model_validator(mode="after")
    def _post_process(self) -> "Settings":
        raw = (self.allowed_origins_raw or "*").strip()
        self.allowed_origins = (
            ["*"] if raw == "*" else [o.strip() for o in raw.split(",") if o.strip()]
        )
        try:
            parsed = make_url(self.database_url)
            if not parsed.drivername.startswith("postgresql"):
                raise ValueError
        except Exception:
            raise ValueError(
                "DATABASE_URL must be a valid PostgreSQL URL "
                "(e.g., postgresql://, postgresql+psycopg2://, postgresql+psycopg://, postgresql+asyncpg://). "
                f"Got: {self.database_url}"
            )
        return self


settings = Settings()
