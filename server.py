
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logger import setup_logging
from src.core.registry import registry
from src.core.config import app_settings
from src.storage.factory import StorageFactory, StorageEngine

from src.server.comics import comic_router
from src.server.archive import archive_router
from src.server.library import library_router

# --- Startup & Setup ---

from src.core.tasks import TaskManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(log_level=logging.DEBUG if app_settings.debug else logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Server starting (debug={app_settings.debug})")
    
    # Initialize Task Manager
    app.state.task_manager = TaskManager()
    
    # Load all provider plugins
    registry.load_all_providers()
    logger.info(f"Providers loaded: {len(registry.get_all())}")
    
    yield
    # Shutdown
    logger.info("Server shutting down, waiting for background tasks...")
    await app.state.task_manager.shutdown()
    logger.info("Server shutdown complete.")

app = FastAPI(
    title="ComicMgr API",
    description="Extensible Comic Management Platform API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---

app.include_router(comic_router)
app.include_router(archive_router)
app.include_router(library_router)
