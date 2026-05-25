import uvicorn
import yaml

if __name__ == "__main__":
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    server = cfg.get("server", {})
    uvicorn.run(
        "backend.main:app",
        host=server.get("host", "127.0.0.1"),
        port=server.get("port", 8000),
        reload=True,
    )
