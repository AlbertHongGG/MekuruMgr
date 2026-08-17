import asyncio
import logging
from typing import Coroutine, Dict, Any, List

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Global asynchronous task manager that tracks background jobs
    and ensures graceful shutdown upon server termination.
    """
    def __init__(self):
        # Maps task_id -> asyncio.Task
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def _task_wrapper(self, task_id: str, coro: Coroutine[Any, Any, Any]) -> None:
        """
        Wraps a coroutine to catch and swallow asyncio.CancelledError,
        preventing nasty traceback leaks on server shutdown.
        """
        try:
            await coro
        except asyncio.CancelledError:
            logger.info(f"Task '{task_id}' gracefully cancelled (system shutdown/interrupt).")
        except Exception as e:
            logger.error(f"Task '{task_id}' failed with error: {e}", exc_info=True)
        finally:
            # Safely remove from active tasks dictionary when completed or errored
            self._active_tasks.pop(task_id, None)

    def submit(self, task_id: str, coro: Coroutine[Any, Any, Any]) -> bool:
        """
        Submit a coroutine to be executed in the background.
        Returns True if task was submitted, False if task_id already exists (ignored).
        """
        if task_id in self._active_tasks:
            logger.info(f"Task '{task_id}' is already running. Ignoring duplicate submission.")
            return False
            
        task = asyncio.create_task(self._task_wrapper(task_id, coro))
        self._active_tasks[task_id] = task
        logger.info(f"Task '{task_id}' submitted successfully.")
        return True

    def get_active_tasks(self) -> List[str]:
        """
        Return a list of active task_ids.
        """
        return list(self._active_tasks.keys())

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a specific active task by its ID.
        Returns True if the task was found and cancelled, False otherwise.
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.cancel()
            logger.info(f"Cancellation requested for task '{task_id}'.")
            return True
        return False

    async def shutdown(self) -> None:
        """
        Cancel all active tasks and wait for them to finish cleanly.
        """
        if not self._active_tasks:
            return

        logger.info(f"Shutting down TaskManager. Cancelling {len(self._active_tasks)} active tasks...")
        
        # Issue cancel to all tasks
        tasks_to_wait = list(self._active_tasks.values())
        for task in tasks_to_wait:
            task.cancel()
            
        # Wait for all tasks to acknowledge cancellation and exit
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)
            
        logger.info("All background tasks have been cleanly terminated.")
