from fastapi import Depends, FastAPI
from dotenv import load_dotenv 
import os
from functools import lru_cache
from typing import Annotated
from starlette.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import structlog

from .core.config import LoggingSettings, OpenAISettings
from .core.exceptions import register_exception_handlers
from .core.logging import setup_logging, LoggingMiddleware

@lru_cache
def get_all_settings():
    return {
        "logging_setting": LoggingSettings(),
        "openai_setting": OpenAISettings()
    }

settings = get_all_settings()

# Logging Setup
# must setup before app is created
setup_logging(
    log_level=settings.get("logging_setting").log_level,
    log_json=settings.get("logging_setting").log_json,
    log_file=settings.get("logging_setting").log_file
)


app = FastAPI()
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")

# CORS Configuration
allowed_origins=[
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_headers=["*"],
    allow_methods=["*"],
    expose_headers=["X-Request-ID"]
)
app.add_middleware(LoggingMiddleware)

# Exception Handler
register_exception_handlers(app)

@app.get("/api/v1/health")
async def get_health():
    return {"health": 100}

# @app.get("/api/v1/info")
# async def get_info(settings: Annotated[Settings, Depends(get_settings)]):
#     return {
#         "api_key": settings.openai_api_key,
#         "model": settings.openai_model
#     }

@app.put("/api/v1/health/{health}")
def get_health_id(health: int):
    return {"health": health}