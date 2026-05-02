from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingest.pipeline import IngestionPipeline
from app.schemas.research import PipelineRunResponse

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/run-pipeline", response_model=PipelineRunResponse)
def run_pipeline(
    query: str = "multimodal agents",
    limit_per_source: int = Query(default=5, ge=1, le=20),
    include_demo: bool = True,
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    pipeline = IngestionPipeline()
    return pipeline.run(db=db, query=query, limit_per_source=limit_per_source, include_demo=include_demo)
