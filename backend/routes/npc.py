from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import NPCInfo, NPCListResponse

router = APIRouter(prefix="/api", tags=["npc"])

_npc_service = None


def init(npc_service):
    global _npc_service
    _npc_service = npc_service


@router.get("/npc", response_model=NPCListResponse)
async def list_npcs():
    npcs = _npc_service.list_npcs()
    return NPCListResponse(npcs=[NPCInfo(**n) for n in npcs])


@router.get("/npc/{npc_id}", response_model=NPCInfo)
async def get_npc(npc_id: str, player_id: str = Query("default")):
    try:
        info = _npc_service.get_npc_info(npc_id, player_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"NPC '{npc_id}' not found")
    return NPCInfo(**info)
