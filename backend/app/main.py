import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging to show up in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
)
logger = logging.getLogger("prism")

from app.api.routes_analysis import router as analysis_router
from app.api.routes_health import router as health_router
from app.api.routes_items import router as items_router
from app.api.routes_memory import router as memory_router
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_reports import router as reports_router
from app.agent.router import router as agent_router
from app.agent.router import start_scheduler, stop_scheduler
from app.core.config import get_settings
from app.db.init_db import init_db

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()


app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(items_router)
app.include_router(pipeline_router)
app.include_router(memory_router)
app.include_router(reports_router)
app.include_router(agent_router)
