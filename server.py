import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from rich.logging import RichHandler

from src.core.container import AppContainer
from src.server.comics import comic_router as comics_router
from src.server.archive import archive_router
from src.server.library import library_router

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)

logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize IoC Container
    container = AppContainer()
    app.state.container = container
    
    logger.info("Starting background services...")
    await container.start()
    
    yield
    
    logger.info("Shutting down background services...")
    await container.stop()
    logger.info("Shutdown complete.")

def create_app() -> FastAPI:
    app = FastAPI(title="ComicMgr Server", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(comics_router)
    app.include_router(archive_router)
    app.include_router(library_router)

    return app

app = create_app()

if __name__ == "__main__":
    # Need to instantiate a temporary container just to get the port
    temp_container = AppContainer()
    uvicorn.run(
        "server:create_app",
        host=temp_container.config.server.host,
        port=temp_container.config.server.port,
        reload=temp_container.config.debug,
        factory=True
    )
