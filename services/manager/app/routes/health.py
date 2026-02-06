from fastapi import APIRouter
from services.common.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service="manager")


@router.get("/ready", response_model=HealthResponse)
async def ready():
    return HealthResponse(status="ok", service="manager")
