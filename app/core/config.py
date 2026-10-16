import json
from functools import lru_cache
from typing import Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # common configurations
    app_name: str = "app name"
    base_url: str = "http://localhost:8000"
    secret_key: str = "your_secret_key"
    algorithm: str = "your_algorithm"
    access_token_expire_minutes: int = 30  # max
    refresh_token_expire_days: int = 90  # max
    signup_otp_expiration_minutes: int = 5  # OTP expiration time in minutes

    resend_api_key: str = "your-resend-api-key"  # to be used for email services

    port1: int = 1111
    port2: int = 1112

    smtp_server: str = "your-smtp-server"
    email_username: str = "your-username"
    email_password: str = "your-email-password"

    api_url: str = "zeptomail api url"
    api_authorization_key: str = "your-authorization-key"

    # environment control → "development" (default) or "production"
    environment: str = "development"

    # ----------------------- DEVELOPMENT ENV CONFIGURATIONS ------------------------- #
    # Origins are normalized to lists by the validators below
    dev_origins: list[str] | str = ["*"]
    dev_db_url: str | None = None
    dev_db_key: str | None = None
    dev_redis_url: str
    backend: str = "redis://localhost:6379/1"
    redis_limiter_url: str = "redis://localhost:6379/2"

    # ----------------------- PRODUCTION ENV CONFIGURATIONS ------------------------- #
    # Origins are normalized to lists by the validators below
    origins: list[str] | str = []
    database_url: str | None = None
    database_key: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env")

    # ---------------------- VALIDATORS ---------------------- #
    @field_validator("environment", mode="before")
    @classmethod
    def _normalize_environment(cls, v: Any) -> str:
        if v is None:
            return "development"
        if isinstance(v, str):
            s = v.strip().strip('"').strip("'")
            return s.lower()
        return str(v).lower()

    @field_validator("dev_origins", mode="before")
    @classmethod
    def _parse_dev_origins(cls, v: Any) -> list[str]:
        return cls._parse_origins_value(v)

    @field_validator("origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: Any) -> list[str]:
        """Normalize ORIGINS from .env into a list."""
        return cls._parse_origins_value(v)

    @staticmethod
    def _parse_origins_value(v: Any) -> list[str]:
        """Normalize origins value from .env into a list of strings.

        Acceptable inputs:
        - a JSON-style list: ["https://a","https://b"]
        - a comma-separated string: "https://a,https://b"
        - a single origin string: "https://a"
        - already a list of strings
        """
        if v is None:
            return []
        if isinstance(v, list):

            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            s = v.strip()
            # try to detect JSON-style list
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            # comma-separated
            if "," in s:
                return [part.strip() for part in s.split(",") if part.strip()]
            if s:
                return [s]
        # fallback: coerce to string
        return [str(v)] if v is not None else []

    # ---------------------- EFFECTIVE VALUES ---------------------- #
    @property
    def effective_redis_url(self) -> Optional[str]:
        """Return the dev redis url when environment is not production.

        If a development value exists and the environment is not production,
        that value is returned; otherwise the production value is returned.
        """
        if self.environment.lower() != "production" and self.dev_redis_url:
            return self.dev_redis_url
        elif self.environment.lower() == "local":
            return 
        return self.redis_url

    @property
    def effective_database_url(self) -> Optional[str]:
        """Return the dev database url when environment is not production.

        If a development value exists and the environment is not production,
        that value is returned; otherwise the production value is returned.
        """
        if self.environment.lower() != "production" and self.dev_db_url:
            return self.dev_db_url
        return self.database_url

    @property
    def effective_database_key(self) -> Optional[str]:
        """Return the dev database key when environment is not production.

        If a development value exists and the environment is not production,
        that value is returned; otherwise the production value is returned.
        """
        if self.environment.lower() != "production" and self.dev_db_key:
            return self.dev_db_key
        return self.database_key

    # ---------------------- EFFECTIVE ORIGINS ---------------------- #
    def allowed_origins(self) -> list[str] | str:
        """Return origins for the active environment.

        This helper makes switching origins simple by reading the `environment`
        setting which can be set via the ENVIRONMENT environment variable.
        """
        return (
            self.origins
            if self.environment.lower() == "production"
            else self.dev_origins
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.environment.title()} environment")
    # print(f"BASE_URL: {settings.base_url}")
    return settings
