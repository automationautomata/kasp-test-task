
from dishka import AsyncContainer, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import AppConfig, WorkersType
from app.di import (
    ExecutorMaxWorkers,
    ExecutorProvider,
    LoggerProvider,
    MaxUploadingUsers,
    SemaphoreProvider,
)
from app.handlers import ChunkSizeMB
from app.infrastructure.di import (
    LemmasCounterProvider,
    StorageProvider,
    StreamWritersProvider,
    XLSXWriterChunkSize,
)
from app.infrastructure.storage import Base
from app.services.di import ServicesProvider


def db_engine(db_dsn: str) -> AsyncEngine:
    return create_async_engine(db_dsn, echo=False)


async def init_db(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def db_cleanup(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def container(config: AppConfig, engine: AsyncEngine) -> AsyncContainer:
    providers = [
        LoggerProvider(),
        ExecutorProvider(),
        SemaphoreProvider(),
        LemmasCounterProvider(),
        StorageProvider(),
        StreamWritersProvider(),
        ServicesProvider(),
    ]
    container = make_async_container(
        *providers,
        context={
            MaxUploadingUsers: config.max_uploading_users,
            ExecutorMaxWorkers: config.max_workers,
            XLSXWriterChunkSize: config.writer_chunk_size_kb,
            ChunkSizeMB: config.upload_chunk_size_mb,
            WorkersType: config.workers_type,
            AsyncEngine: engine,
        },
    )
    return container
