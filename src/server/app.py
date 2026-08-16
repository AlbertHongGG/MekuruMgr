from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.core.logger import setup_logging
from src.core.registry import registry
from src.server.routers import comics, archive

# Dynamically discover and load all providers
registry.load_all_providers()

# Initialize global logging format
setup_logging()

app = FastAPI(
    title="ComicMgr API",
    description="A highly extensible, plugin-based Comic Management Server",
    version="1.0.0"
)

# Mount local data directory as static media files
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory="data"), name="media")

# Register all API routers
app.include_router(comics.router)
app.include_router(archive.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
