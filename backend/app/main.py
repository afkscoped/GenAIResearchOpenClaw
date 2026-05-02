from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analysis import router as analysis_router
from app.api.routes_health import router as health_router
from app.api.routes_items import router as items_router
from app.api.routes_memory import router as memory_router
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_reports import router as reports_router
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


app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(items_router)
app.include_router(pipeline_router)
app.include_router(memory_router)
app.include_router(reports_router)
