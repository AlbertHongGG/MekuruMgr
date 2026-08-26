
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logger import setup_logging
from src.core.registry import registry
from src.core.config import app_settings
from src.storage.factory import StorageFactory

from src.server.comics import comic_router
from src.server.archive import archive_router
from src.server.library import library_router

# --- Startup & Setup ---

from src.application.queue_service import DownloadQueueService
from src.application.comic_manager import ComicManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(log_level=logging.DEBUG if app_settings.debug else logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Server starting (debug={app_settings.debug})")
    
    # Load all provider plugins
    registry.load_all_providers()
    logger.info(f"Providers loaded: {len(registry.get_all())}")
    
    # Initialize Queue Service
    provider = StorageFactory.get_provider()
    app.state.queue_service = DownloadQueueService(
        manager=ComicManager(),
        library_storage=provider.get_library_storage(),
        task_storage=provider.get_task_storage(),
        media_storage=provider.get_media_storage()
    )
    app.state.queue_service.start()
    
    yield
    # Shutdown
    logger.info("Server shutting down, waiting for background tasks...")
    if hasattr(app.state, 'queue_service'):
        await app.state.queue_service.stop()
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
