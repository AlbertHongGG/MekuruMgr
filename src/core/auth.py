import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class Signer(ABC):
    """Abstract interface for signature generation."""
    
    @abstractmethod
    def generate_signature(self, endpoint: str, params: Dict[str, Any]) -> Tuple[int, str]:
        """
        Generate requestTime and sign based on parameters.
        Returns:
            Tuple containing (requestTime: int, sign: str)
        """
        pass

class DummySigner(Signer):
    """
    A placeholder signer.
    In a real scenario, this would be replaced with the actual reverse-engineered logic.
    """
    def generate_signature(self, endpoint: str, params: Dict[str, Any]) -> Tuple[int, str]:
        # Return exact recorded signatures from test.json for testing
        if "detail_page" in endpoint:
            return 1786876141902, "d959026a57daeeecb0fc2baa202cf7fe"
        elif "chapter_list" in endpoint:
            return 1786876141901, "2da1da77c91c5c9b8f08a8bb75387f52"
        elif "read" in endpoint: # assuming this is for chapter 1
            return 1786876146137, "4487a585bce41c4c9553d54cb1fc0372"
            
        request_time = int(time.time() * 1000)
        return request_time, "dummy"
