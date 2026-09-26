from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import APP_HOST, APP_PORT, CORS_ORIGINS
from app.routers.health import router as health_router
from app.routers.query import router as query_router
from app.routers.preview import router as preview_router

app = FastAPI(title="SatQuery AI Backend", version="1.0.0", description="SIH 26167 backend for multimodal remote-sensing analysis.")
allow_origins = ["*"] if "*" in CORS_ORIGINS else CORS_ORIGINS
app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_credentials=False if "*" in allow_origins else True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health_router)
app.include_router(query_router)
app.include_router(preview_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
