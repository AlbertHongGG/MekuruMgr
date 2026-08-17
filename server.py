import structlog
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(log_level=logging.DEBUG if app_settings.debug else logging.INFO)
    logger = structlog.get_logger(__name__)
    logger.info("server_starting", debug=app_settings.debug)
    
    # Load all provider plugins
    registry.load_all_providers()
    logger.info("providers_loaded", count=len(registry.list_providers()))
    
    yield
    # Shutdown
    logger.info("server_shutting_down")

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
