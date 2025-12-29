from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str
    SYNC_DB_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_SECONDS: int

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str

    REDIS_HOST: str
    REDIS_PORT: str


    TEMPLATE_FOLDER: ClassVar[Path] = Path(__file__).parent / 'templates'

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

config = Settings()
