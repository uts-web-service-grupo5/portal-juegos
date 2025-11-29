import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    environment: str = "dev"
    user_db_url: str = f"sqlite:///{BASE_DIR / 'users.db'}"
    subscription_db_url: str = f"sqlite:///{BASE_DIR / 'subscriptions.db'}"
    transaction_db_url: str = f"sqlite:///{BASE_DIR / 'transactions.db'}"
    catalog_db_url: str = f"sqlite:///{BASE_DIR / 'catalog.db'}"

    soap_url: str = "http://localhost:8000/soap/v1"
    api_key: str | None = None
    secret_key: str = "dev-secret-key"
    log_level: str = "INFO"


settings = Settings()
