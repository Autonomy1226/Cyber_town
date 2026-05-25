from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/player", tags=["player"])

_economy_service = None


def init(economy_service):
    global _economy_service
    _economy_service = economy_service


class InventoryResponse(BaseModel):
    items: list[dict]
    money: int


class ItemAction(BaseModel):
    player_id: str
    item_id: str


@router.get("/{player_id}", response_model=InventoryResponse)
async def get_player(player_id: str):
    p = _economy_service.get_player(player_id)
    return InventoryResponse(items=p.get_inventory(), money=p.money)
