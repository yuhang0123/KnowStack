from fastapi import Depends, FastAPI
from dotenv import load_dotenv 
import os
from .core.config import Settings
from functools import lru_cache
from typing import Annotated

app = FastAPI()
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")

@lru_cache
def get_settings():
    return Settings()

@app.get("/api/v1/health")
async def get_health():
    return {"health": 100}

@app.get("/api/v1/info")
async def get_info(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model
    }