import asyncio
import logging
from typing import Coroutine, Set, Any

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Global asynchronous task manager that tracks background jobs
    and ensures graceful shutdown upon server termination.
    """
    def __init__(self):
        self._active_tasks: Set[asyncio.Task[Any]] = set()

    async def _task_wrapper(self, coro: Coroutine[Any, Any, Any]) -> None:
        """
        Wraps a coroutine to catch and swallow asyncio.CancelledError,
        preventing nasty traceback leaks on server shutdown.
        """
        try:
            await coro
        except asyncio.CancelledError:
            logger.info("Background task gracefully cancelled (system shutdown/interrupt).")
            # Swallow the exception so the event loop doesn't print a traceback
        except Exception as e:
            logger.error(f"Background task failed with error: {e}", exc_info=True)

    def submit(self, coro: Coroutine[Any, Any, Any]) -> None:
        """
        Submit a coroutine to be executed in the background.
        """
        # Create the task through the wrapper
        task = asyncio.create_task(self._task_wrapper(coro))
        self._active_tasks.add(task)
        # Remove task from active set when done to prevent memory leaks
        task.add_done_callback(self._active_tasks.discard)

    async def shutdown(self) -> None:
        """
        Cancel all active tasks and wait for them to finish cleanly.
        """
        if not self._active_tasks:
            return

        logger.info(f"Shutting down TaskManager. Cancelling {len(self._active_tasks)} active tasks...")
        
        # Issue cancel to all tasks
        for task in self._active_tasks:
            task.cancel()
            
        # Wait for all tasks to acknowledge cancellation and exit
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            
        logger.info("All background tasks have been cleanly terminated.")
