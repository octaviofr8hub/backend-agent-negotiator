"""
API Gateway configuration.
Environment variables for LiveKit, CORS, and service settings.
"""
import os
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings
from typing import List, Literal, Union, Any
from pydantic import AnyUrl, parse_obj_as, validator, Field
from pydantic import PostgresDsn

def parse_cors(value: Any) -> List[AnyUrl]:
    # print(f"Raw BACKEND_CORS_ORIGINS value: {value}")
    if isinstance(value, str) and not value.startswith("["):
        urls = [i.strip() for i in value.split(",")]
        # print(f"Split URLs: {urls}")
        result = parse_obj_as(List[AnyUrl], urls)
        # print(f"Parsed URLs: {result}")
        return result
    elif isinstance(value, list):
        return parse_obj_as(List[AnyUrl], value)
    elif isinstance(value, AnyUrl):
        return [value]
    raise ValueError(f"Formato inválido para BACKEND_CORS_ORIGINS: {value}")

class Settings(BaseSettings):
    """Environment variables for the API Gateway."""

    # ── LiveKit ──
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    CORS_ORIGINS: Union[List[AnyUrl], str] = []
    @validator("CORS_ORIGINS", pre=True)
    def validate_cors(cls, value: Any) -> List[AnyUrl]:
        return parse_cors(value)

    # ── Room Monitor ──
    ROOM_POLL_INTERVAL: int = 10       # Seconds between room polls
    CARRIER_JOIN_TIMEOUT: int = 60     # Seconds waiting for carrier to answer
    CALL_MAX_DURATION: int = 600       # Max call duration (10 min)
    CALL_SETTLE_DELAY: int = 15        # Wait after carrier disconnects
    # ── Environment ──
    ENVIRONMENT: Literal["local", "qa", "production"] = "local"
    DEBUG: bool = True

    # Database
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_SERVER: str
    POSTGRESQL_PORT: int
    POSTGRESQL_DB: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRESQL_USER,
            password=self.POSTGRESQL_PASSWORD,
            host=self.POSTGRESQL_SERVER,
            port=self.POSTGRESQL_PORT,
            path=self.POSTGRESQL_DB,
        )

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        )
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
