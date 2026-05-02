from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.reports.markdown_report import generate_weekly_brief

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/weekly.md")
def weekly_markdown_report(db: Session = Depends(get_db)) -> Response:
    markdown = generate_weekly_brief(db)
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=prism-weekly-brief.md"},
    )
