from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # These names must match exactly what's in your .env file
    DATABASE_URL: str = "sqlite:///./smartcurbs.db"
    APP_ENV: str = "development"
    APP_TITLE: str = "Aswan SmartCurbs AI"
    APP_VERSION: str = "0.1.0"
    AUTH_SECRET_KEY: str = "change-this-development-secret-key"
    AUTH_ALGORITHM: Literal["HS256"] = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # Ignore any extra variables in .env
    )

    @field_validator("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero"
            )
        return value

    @model_validator(mode="after")
    def validate_production_auth_settings(self):
        if self.APP_ENV.lower() == "production":
            secret = self.AUTH_SECRET_KEY.strip()
            if (
                len(secret) < 32
                or secret == "change-this-development-secret-key"
                or secret.lower().startswith("replace-with-")
            ):
                raise ValueError(
                    "AUTH_SECRET_KEY must be a secure production secret "
                    "of at least 32 characters and must not be a placeholder"
                )
        return self


# Single shared instance — import this everywhere
settings = Settings()