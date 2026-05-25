from fastapi import APIRouter, Query

from backend.models.schemas import LogResponse, LogEntry

router = APIRouter(prefix="/api", tags=["logs"])

_log_service = None


def init(log_service):
    global _log_service
    _log_service = log_service


@router.get("/logs", response_model=LogResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    npc_id: str | None = Query(None),
):
    entries = _log_service.query_logs(limit=limit, npc_id=npc_id)
    return LogResponse(
        total=len(entries),
        entries=[LogEntry(**e) for e in entries],
    )
