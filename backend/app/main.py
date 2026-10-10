from fastapi import FastAPI
from dotenv import load_dotenv 
import os

app = FastAPI()
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")

@app.get("/api/v1/health")
async def get_health():
    return {"health": 100}