import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.db.session import init_db
from backend.app.api.events import router as events_router
from backend.app.api.runs import router as runs_router
from backend.app.api.layers import router as layers_router
from backend.app.api.findings import router as findings_router
from backend.app.api.simulations import router as simulations_router
from backend.app.api.receipts import router as receipts_router
from backend.app.api.research import router as research_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("terrasentinel")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TerraSentinel database and tables...")
    init_db()
    logger.info("TerraSentinel Intelligence Engine ready.")
    yield
    logger.info("TerraSentinel backend shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-Grounded Satellite Intelligence for Flood Disaster Response",
    version="1.2.0",
    lifespan=lifespan
)

# Enable CORS for local frontend workbench
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
api_v1 = FastAPI()
api_v1.include_router(events_router)
api_v1.include_router(runs_router)
api_v1.include_router(layers_router)
api_v1.include_router(findings_router)
api_v1.include_router(simulations_router)
api_v1.include_router(receipts_router)
api_v1.include_router(research_router)

app.mount(settings.API_V1_STR, api_v1)

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": "1.2.0",
        "environment": "WINDOWS_11_COMPATIBLE"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
