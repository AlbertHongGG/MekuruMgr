from abc import ABC, abstractmethod

class IProgressObserver(ABC):
    """
    Observer interface for tracking comic sync progress.
    Implement this to bridge backend sync events to a UI (like CLI rich progress or SSE).
    """
    
    @abstractmethod
    def on_sync_start(self, total_chapters: int):
        pass

    @abstractmethod
    def on_chapter_start(self, chapter_id: str, chapter_title: str, total_pages: int):
        pass

    @abstractmethod
    def on_page_downloaded(self, chapter_id: str, page_index: int):
        pass

    @abstractmethod
    def on_chapter_complete(self, chapter_id: str):
        pass

    @abstractmethod
    def on_sync_complete(self):
        pass
