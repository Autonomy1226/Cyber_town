from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import yaml
import os

from helloagents import LLMClient, LLMConfig
from backend.services.npc_service import NPCService
from backend.services.log_service import LogService
from backend.routes import chat, npc, logs, actions, npc_chat
from backend.services.action_service import ActionService


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    data_dir = cfg.get("data_dir", "backend/data")

    log_service = LogService(data_dir)

    llm_config = LLMConfig(
        base_url=cfg["llm"]["base_url"],
        api_key=os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", cfg["llm"].get("api_key", ""))),
        model=cfg["llm"]["model"],
        embedding_model=cfg["llm"]["embedding_model"],
        temperature=cfg["llm"]["temperature"],
        max_tokens=cfg["llm"]["max_tokens"],
    )
    llm_client = LLMClient(llm_config)

    npc_service = NPCService(
        llm_client,
        use_qdrant=cfg.get("qdrant", {}).get("enabled", False),
        qdrant_url=cfg.get("qdrant", {}).get("url", ""),
    )

    action_service = ActionService()

    chat.init(npc_service, log_service)
    npc.init(npc_service)
    logs.init(log_service)
    actions.init(action_service)
    npc_chat.init(npc_service, action_service)

    app.state.npc_service = npc_service
    app.state.log_service = log_service
    app.state.llm_client = llm_client

    yield

    await llm_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="CyberTown API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(chat.router)
    app.include_router(actions.router)
    app.include_router(npc_chat.router)
    app.include_router(npc.router)
    app.include_router(logs.router)

    return app


app = create_app()
