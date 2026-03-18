from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.services import ExportFormats
from app.services.ports import (
    LemmasCounterProtocol,
    StatisticsStorageProtocol,
    StreamWriter,
)

from .lemmatizer import Pymorphy3LemmasCounter
from .storage import DBStatisticsStorage
from .writer import XLSXStreamWriter

XLSXWriterChunkSize = int


class LemmasCounterProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def lemmas_counter(self) -> LemmasCounterProtocol:
        return Pymorphy3LemmasCounter()


class StorageProvider(Provider):
    engine = from_context(AsyncEngine, scope=Scope.APP)

    @provide(scope=Scope.APP)
    async def session(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    def statistics_storage(
        self, sessionmaker: async_sessionmaker[AsyncSession]
    ) -> StatisticsStorageProtocol:
        return DBStatisticsStorage(sessionmaker)


class StreamWritersProvider(Provider):
    chunk_size = from_context(XLSXWriterChunkSize, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def streaming_writer(
        self, chunk_size: XLSXWriterChunkSize
    ) -> dict[ExportFormats, StreamWriter]:
        return {ExportFormats.XLSX: XLSXStreamWriter(chunk_size)}
