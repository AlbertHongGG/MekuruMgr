from enum import Enum

class BuiltinProvider(str, Enum):
    """
    Strongly-typed String Enum for Built-in Providers.
    Using this provides IDE auto-completion and prevents typos.
    
    Note: External plugins do NOT need to add themselves to this enum.
    They can simply pass their string ID directly to the manager.
    """
    COMICWIFI = "comicwifi"
