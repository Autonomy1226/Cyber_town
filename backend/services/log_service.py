import logging
import logging.handlers
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class LogService:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        log_dir = self._data_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "cybertown.log", maxBytes=5_000_000, backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        ))

        sqlite_handler = _SQLiteLogHandler(self._data_dir / "cybertown.db")
        sqlite_handler.setLevel(logging.INFO)

        root = logging.getLogger("cybertown")
        root.setLevel(logging.DEBUG)
        root.addHandler(file_handler)
        root.addHandler(console_handler)
        root.addHandler(sqlite_handler)

    def query_logs(self, limit: int = 50, npc_id: str | None = None) -> list[dict]:
        db_path = self._data_dir / "cybertown.db"
        if not db_path.exists():
            return []
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if npc_id:
            cur.execute(
                "SELECT * FROM logs WHERE npc_id = ? ORDER BY timestamp DESC LIMIT ?",
                (npc_id, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]


class _SQLiteLogHandler(logging.Handler):
    def __init__(self, db_path: str):
        super().__init__()
        self._db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                event TEXT NOT NULL,
                npc_id TEXT,
                player_id TEXT,
                detail TEXT
            )
        """)
        conn.commit()
        conn.close()

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                data = {"event": record.msg % record.args if record.args else record.msg}

            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO logs (timestamp, level, event, npc_id, player_id, detail) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    record.levelname,
                    str(data.get("event", "")),
                    str(data.get("npc_id", "")) if data.get("npc_id") else None,
                    str(data.get("player_id", "")) if data.get("player_id") else None,
                    str(data.get("detail", "")) if data.get("detail") else None,
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            self.handleError(record)
