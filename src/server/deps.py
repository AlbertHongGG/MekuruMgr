from fastapi import Request, Depends, HTTPException
from src.core.registry import registry

def get_container(request: Request):
    return request.app.state.container

def get_comic_manager(request: Request):
    return request.app.state.container.comic_manager

def get_library_service(request: Request):
    return request.app.state.container.library_service

def resolve_provider(provider_id: str) -> str:
    try:
        return registry.resolve_id(provider_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
