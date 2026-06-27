"""
Centralized FastAPI dependency factories.

All route files should import dependency functions from here rather than
defining their own ``get_memory_service()`` helpers. This prevents drift
between route modules and ensures a single place to update session wiring.

Usage in route files:
    from api.dependencies import get_memory_service
    ...
    async def my_route(memory_service: MemoryService = Depends(get_memory_service)):
        ...
"""

from services.memory_service import MemoryService
from models.database import async_session


def get_memory_service() -> MemoryService:
    """Return a MemoryService wired to the application session factory.

    The factory (``async_session``) is passed rather than an open session,
    so MemoryService can create short-lived sessions for each DB operation.
    """
    return MemoryService(async_session)
