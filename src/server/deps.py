from fastapi import HTTPException
from src.core.registry import registry
from src.domain.exceptions import AppBaseError

def resolve_provider_id(provider_id: str) -> str:
    """FastAPI Dependency to resolve provider aliases to their primary ID."""
    try:
        return registry.resolve_id(provider_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
