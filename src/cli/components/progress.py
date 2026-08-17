from rich.progress import Progress, TaskID, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from src.application.interfaces import IProgressObserver

class RichProgressObserver(IProgressObserver):
    """
    Rich CLI Implementation of the Sync Progress Observer.
    Renders detailed progress bars to standard output.
    """
    def __init__(self):
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        )
        self.sync_task: TaskID = None
        self.chapter_task: TaskID = None

    def on_sync_start(self, total_chapters: int):
        self.progress.start()
        self.sync_task = self.progress.add_task(f"[bold green]Total Sync Progress", total=total_chapters)

    def on_chapter_start(self, chapter_id: str, chapter_title: str, total_pages: int):
        if self.chapter_task is not None:
            self.progress.remove_task(self.chapter_task)
        self.chapter_task = self.progress.add_task(f"[cyan]Downloading {chapter_title}", total=total_pages)

    def on_page_downloaded(self, chapter_id: str, page_index: int):
        if self.chapter_task is not None:
            self.progress.advance(self.chapter_task)

    def on_chapter_complete(self, chapter_id: str):
        if self.sync_task is not None:
            self.progress.advance(self.sync_task)
        if self.chapter_task is not None:
            self.progress.remove_task(self.chapter_task)
            self.chapter_task = None

    def on_sync_complete(self):
        self.progress.stop()
