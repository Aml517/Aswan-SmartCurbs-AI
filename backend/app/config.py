from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # These names must match exactly what's in your .env file
    DATABASE_URL: str
    APP_ENV: str = "development"
    APP_TITLE: str = "Aswan SmartCurbs AI"
    APP_VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # Ignore any extra variables in .env
    )


# Single shared instance — import this everywhere
settings = Settings()