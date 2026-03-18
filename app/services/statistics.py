import asyncio
import logging
import uuid
from concurrent.futures import Executor
from typing import Awaitable

from app.models import Chunk, ChunkReader

from .ports import LemmasCounterProtocol, LemmasStatistics, StatisticsStorageProtocol


class WordFormStatisticsError(Exception): ...


class WordFormStatistics:
    def __init__(
        self,
        lemma_counter: LemmasCounterProtocol,
        stat_storage: StatisticsStorageProtocol,
        executor: Executor,
        batch_size: int | None,
        logger: logging.Logger,
    ):
        self.lemma_counter = lemma_counter
        self.stat_storage = stat_storage
        self.executor = executor
        self.batch_size = batch_size
        self.logger = logger

    async def collect_statistics(self, chunk_reader: ChunkReader) -> str:
        try:
            queue = asyncio.Queue(maxsize=self.batch_size if self.batch_size else 0)

            sem = None
            if self.batch_size and self.batch_size != 0:
                sem = asyncio.Semaphore(self.batch_size)

            key = uuid.uuid4().hex
            saver_task = asyncio.create_task(self.__saver(queue, key))

            async with asyncio.TaskGroup() as tg:
                async for chunk in chunk_reader:
                    coro = self.__lemmas_count_task(chunk, queue)
                    tg.create_task(self.__make_runner(coro, sem))

            await queue.join()
            await queue.put(None)
            await saver_task

            return key
        except Exception as e:
            asyncio.create_task(self.__cleanup(key))  # noqa: RUF006
            raise WordFormStatisticsError() from e

    async def __lemmas_count_task(self, chunk: Chunk, queue: asyncio.Queue):
        loop = asyncio.get_running_loop()
        lemmas_count = await loop.run_in_executor(
            self.executor, self.lemma_counter.count_lemmas, chunk.data
        )
        await queue.put(LemmasStatistics(chunk.ind, lemmas_count, chunk.is_line_ends))

    async def __saver(self, queue: asyncio.Queue, key):
        stats = []
        while True:
            stat: LemmasStatistics | None = await queue.get()

            if stat is None:
                break

            stats.append(stat)
            if len(stats) >= self.batch_size and self.batch_size != 0:
                await self.stat_storage.save(key, stats)
                stats.clear()

            queue.task_done()

        await self.stat_storage.save(key, stats)
        queue.task_done()

    async def __cleanup(self, key: str):
        try:
            await self.stat_storage.cleanup(key)
        except Exception as e:
            self.logger.error(
                f"DB cleanup failed: key {key}, error: {e}", exc_info=True
            )

    @staticmethod
    async def __make_runner(work: Awaitable, sem: asyncio.Semaphore | None):
        if not sem:
            await work
            return

        async with sem:
            await work
