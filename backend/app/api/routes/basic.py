from fastapi import APIRouter

router = APIRouter(
    prefix="/basic",
    tags=["Basic"]
)

@router.get("/health")
async def get_health():
    return {"health": 100}

@router.put("/health/{health}")
def get_health_id(health: int):
    return {"health": health}