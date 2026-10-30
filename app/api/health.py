from fastapi import APIRouter
from ..schemas import HealthOut
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
@router.get("/health/", response_model=HealthOut, include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "northstar-market"}
