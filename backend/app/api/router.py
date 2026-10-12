from fastapi import APIRouter
from .routes import basic

api_router = APIRouter()

api_router.include_router(basic.router)

