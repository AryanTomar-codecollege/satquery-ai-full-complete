from fastapi import APIRouter

from app.config import EARTHDIAL_MODEL, kaggle_url_configured
from app.services.kaggle_client import health as kaggle_health

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SatQuery AI backend",
        "model": EARTHDIAL_MODEL,
        "kaggle_configured": kaggle_url_configured(),
    }

@router.get("/api/model/health")
def model_health():
    if not kaggle_url_configured():
        return {
            "status": "unavailable",
            "configured": False,
            "model": EARTHDIAL_MODEL,
        }
    result = kaggle_health()
    if result is None:
        return {
            "status": "unavailable",
            "configured": True,
            "model": EARTHDIAL_MODEL,
        }
    result["configured"] = True
    return result
