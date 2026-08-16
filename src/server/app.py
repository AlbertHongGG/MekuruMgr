from fastapi import FastAPI
from src.core.logger import setup_logging
from src.core.registry import registry
from src.server.routers import comics

# Dynamically discover and load all providers
registry.load_all_providers()

# Initialize global logging format
setup_logging()

app = FastAPI(
    title="ComicMgr API",
    description="A highly extensible, plugin-based Comic Management Server",
    version="1.0.0"
)

# Register all API routers
app.include_router(comics.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
