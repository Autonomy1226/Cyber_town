from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.economy_service import interact_object, INTERACTABLE_OBJECTS

router = APIRouter(prefix="/api/object", tags=["objects"])

_economy_service = None


def init(economy_service):
    global _economy_service
    _economy_service = economy_service


class InteractRequest(BaseModel):
    player_id: str
    object_id: str
    action: str


class ObjectInfo(BaseModel):
    object_id: str
    name: str
    actions: list[dict]


@router.get("/list")
async def list_objects():
    result = []
    for oid, obj in INTERACTABLE_OBJECTS.items():
        actions = [{"action": a["action"], "label": a["label"]} for a in obj["actions"]]
        result.append({"object_id": oid, "name": obj["name"], "actions": actions})
    return {"objects": result}


@router.post("/interact")
async def interact(req: InteractRequest):
    result = interact_object(req.player_id, req.object_id, req.action, _economy_service)
    return result
