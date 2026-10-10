"""
Files to implement configuration
"""
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str

    # instead of passing global values while starting up the server, take the values from .env file
    model_config = SettingsConfigDict(env_file=".env")