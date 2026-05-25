from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["actions"])

_action_service = None


def init(action_service):
    global _action_service
    _action_service = action_service


class NPCActionOut(BaseModel):
    npc_id: str
    action_type: str
    target_id: str
    target_position: list[float]
    dialogue_line: str
    duration: float


class ActionsResponse(BaseModel):
    actions: list[NPCActionOut]


@router.get("/npc/actions", response_model=ActionsResponse)
async def get_actions():
    actions = _action_service.get_all_actions()
    return ActionsResponse(actions=[NPCActionOut(**a) for a in actions])
