from fastapi import APIRouter, HTTPException
import logging
import time
import json

from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])

_npc_service = None
_log_service = None


def init(npc_service, log_service):
    global _npc_service, _log_service
    _npc_service = npc_service
    _log_service = log_service


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger = logging.getLogger("cybertown.chat")
    start = time.perf_counter()

    logger.info(json.dumps({
        "event": "chat_request",
        "player_id": request.player_id,
        "npc_id": request.npc_id,
        "detail": request.message[:100],
    }))

    try:
        agent = _npc_service.get_agent(request.npc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"NPC '{request.npc_id}' not found")

    fav = _npc_service.get_favorability(request.npc_id, request.player_id)
    agent.favorability = fav

    # Preload history into short-term memory if this is the first chat this session
    _npc_service.preload_memory(request.npc_id, request.player_id)

    response = await agent.respond(request.message, request.context)

    # Persist favorability
    _npc_service.save_favorability(request.player_id, request.npc_id)

    elapsed = time.perf_counter() - start

    logger.info(json.dumps({
        "event": "chat_response",
        "player_id": request.player_id,
        "npc_id": request.npc_id,
        "detail": response.reply[:100],
        "favorability_delta": response.favorability_change,
        "latency_ms": round(elapsed * 1000, 1),
    }))

    return ChatResponse(
        npc_id=response.npc_id,
        npc_name=response.npc_name,
        reply=response.reply,
        favorability_change=response.favorability_change,
        favorability_current=response.favorability_current,
        favorability_level=response.favorability_level,
        timestamp=time.time(),
    )
