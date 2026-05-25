from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import json
from pathlib import Path

router = APIRouter(prefix="/api/history", tags=["history"])

DATA_DIR = Path("backend/data")
DB_PATH = DATA_DIR / "cybertown.db"


def _ensure_table():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            npc_id TEXT NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_player_npc
        ON chat_history(player_id, npc_id)
    """)
    conn.commit()
    conn.close()


_ensure_table()


class HistoryMessage(BaseModel):
    role: str
    text: str


class SaveRequest(BaseModel):
    player_id: str
    npc_id: str
    messages: list[HistoryMessage]


class SaveResponse(BaseModel):
    saved: int


class LoadResponse(BaseModel):
    messages: list[HistoryMessage]


@router.post("/save", response_model=SaveResponse)
async def save_history(req: SaveRequest):
    conn = sqlite3.connect(str(DB_PATH))
    # Replace entire history for this player+npc pair
    conn.execute(
        "DELETE FROM chat_history WHERE player_id = ? AND npc_id = ?",
        (req.player_id, req.npc_id),
    )
    count = 0
    for msg in req.messages:
        conn.execute(
            "INSERT INTO chat_history (player_id, npc_id, role, text) VALUES (?, ?, ?, ?)",
            (req.player_id, req.npc_id, msg.role, msg.text),
        )
        count += 1
    conn.commit()
    conn.close()
    return SaveResponse(saved=count)


@router.get("/load/{player_id}/{npc_id}", response_model=LoadResponse)
async def load_history(player_id: str, npc_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "SELECT role, text FROM chat_history WHERE player_id = ? AND npc_id = ? ORDER BY id ASC",
        (player_id, npc_id),
    )
    rows = cur.fetchall()
    conn.close()
    return LoadResponse(messages=[HistoryMessage(role=r[0], text=r[1]) for r in rows])
