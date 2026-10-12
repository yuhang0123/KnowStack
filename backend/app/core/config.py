"""
Files to implement configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class LogLevel(str, Enum):
    INFO="INFO"
    DEBUG="DEBUG"
    WARNING="WARNING"
    ERROR="ERROR"
    CRITICAL="CRITICAL"

class Settings(BaseSettings):

    # instead of passing global values while starting up the server, take the values from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class LoggingSettings(Settings):
    log_level: str = LogLevel.INFO
    log_json: bool = True
    log_file: str | None = None

class OpenAISettings(Settings):
    openai_api_key: str
    openai_model: str