from fastapi import HTTPException, status
import asyncio
import time
from sqlalchemy import select

from api.connections.database_connection import get_async_db_session
from api.constants.codes import IntegrationCodes
from api.models.integration import Integration


_INTEGRATION_ORM_TTL_SECONDS = 300
_integration_orm_cache = {}
_integration_orm_lock = asyncio.Lock()


async def call_database(provider: IntegrationCodes, client_id: str):
    async for db in get_async_db_session():
        result = await db.execute(
            select(Integration).where(
                Integration.client_id == client_id,
                Integration.provider == provider,
            )
        )
        integration = result.scalar_one_or_none()
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        db.expunge(integration)
        return integration

async def get_integration_orm(provider: IntegrationCodes, client_id:str):
    now = time.time()
    cache_key = (provider, client_id)
    cached = _integration_orm_cache.get(cache_key)
    if cached and cached[1] > now:
        return cached[0]

    async with _integration_orm_lock:
        now = time.time()
        cached = _integration_orm_cache.get(cache_key)
        if cached and cached[1] > now:
            return cached[0]

        integration = await call_database(provider=provider, client_id=client_id)
        _integration_orm_cache[cache_key] = (integration, now + _INTEGRATION_ORM_TTL_SECONDS)
        return integration