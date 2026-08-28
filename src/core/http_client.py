import httpx
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Hook function signature: fn(provider_id: str, url: str, json_data: dict)
ResponseHook = Callable[[str, str, Dict[str, Any]], None]

class BaseHttpClient:
    """
    A foundational HTTP client designed for the comic manager.
    It provides an Interceptor (Hook) architecture at the application layer,
    allowing test frameworks or metric loggers to hook into the parsed JSON data.
    """

    _global_hooks: list[ResponseHook] = []

    @classmethod
    def add_global_hook(cls, hook: ResponseHook):
        if hook not in cls._global_hooks:
            cls._global_hooks.append(hook)

    @classmethod
    def clear_global_hooks(cls):
        cls._global_hooks.clear()

    def __init__(self, provider_id: str, base_url: str = "", verify: bool = True, timeout: float = 15.0):
        self.provider_id = provider_id
        self.client = httpx.Client(
            base_url=base_url,
            verify=verify,
            timeout=httpx.Timeout(timeout)
        )
        self.hooks: list[ResponseHook] = []
        
    def add_hook(self, hook: ResponseHook):
        """Register a hook that will be called with the fully decrypted/parsed JSON payload."""
        if hook not in self.hooks:
            self.hooks.append(hook)
            
    def notify_hooks(self, url: str, json_data: Dict[str, Any]):
        """Trigger all registered hooks with the final JSON data."""
        for hook in list(self.hooks) + self._global_hooks:
            try:
                hook(self.provider_id, url, json_data)
            except Exception as e:
                logger.error(f"Error in HTTP hook for {self.provider_id}: {e}")

    def close(self):
        self.client.close()
