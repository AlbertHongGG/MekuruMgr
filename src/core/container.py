import logging
from typing import Dict, Any

from src.core.config import AppConfig
from src.core.registry import registry
from src.core.provider import BaseComicProvider
from src.application.comic_manager import ComicManager
from src.application.library_service import LibraryService
from src.application.archive_engine import ArchiveEngine
from src.storage.factory import StorageFactory

logger = logging.getLogger(__name__)

class AppContainer:
    def __init__(self):
        self.config = AppConfig()
        
        # 1. Storage Layer
        self.storage_factory = StorageFactory(self.config.storage)
        self.task_storage = self.storage_factory.get_task_storage()
        self.library_storage = self.storage_factory.get_library_storage()
        self.media_storage = self.storage_factory.get_media_storage()
        
        # 2. Domain/Provider Layer
        registry.load_all_providers()
        self.providers: Dict[str, BaseComicProvider] = {}
        
        for p_id, p_class in registry.get_all_classes().items():
            config_class = getattr(p_class, 'get_config_class', lambda: None)()
            if config_class:
                provider_config = config_class()
                provider_instance = p_class(config=provider_config)
            else:
                try:
                    provider_instance = p_class()
                except TypeError:
                    provider_instance = p_class(http_client=None)
            
            self.providers[p_id] = provider_instance
            
        # 3. Application Services
        self.comic_manager = ComicManager()
        self.comic_manager._providers = self.providers
        self.comic_manager.provider_registry = registry
        if self.config.default_provider:
            self.comic_manager.use(self.config.default_provider)
            
        self.library_service = LibraryService(
            library_storage=self.library_storage,
            task_storage=self.task_storage,
            media_storage=self.media_storage
        )
        
        self.archive_engine = ArchiveEngine(
            manager=self.comic_manager,
            library_storage=self.library_storage,
            task_storage=self.task_storage,
            media_storage=self.media_storage,
            worker_count=self.config.engine.worker_count,
            max_concurrent_tasks=self.config.engine.max_concurrent_tasks
        )

    async def start(self):
        await self.archive_engine.start()
        
    async def stop(self):
        await self.archive_engine.stop()
