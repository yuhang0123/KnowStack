from fastapi import Depends, FastAPI
from dotenv import load_dotenv 
import os
from functools import lru_cache
from typing import Annotated
from starlette.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .core.config import Settings
from .core.exceptions import register_exception_handlers

app = FastAPI()
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")

# CORS Configuration
allowed_origins=[
    "http://localhost:8080"
]

# Exception Handler
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_headers=["*"],
    allow_methods=["*"]
)

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