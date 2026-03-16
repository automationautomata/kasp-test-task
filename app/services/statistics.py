import asyncio
import uuid
from concurrent.futures import Executor

from app.models import Chunk, ChunkReader

from .ports import LemmasCounterProtocol, LemmasStatistics, StatisticsStorageProtocol


class WordFormStatisticsError(Exception): ...


class WordFormStatistics:
    def __init__(
        self,
        lemma_counter: LemmasCounterProtocol,
        stat_storage: StatisticsStorageProtocol,
        executor: Executor,
    ):
        self.lemma_counter = lemma_counter
        self.stat_storage = stat_storage
        self.executor = executor

    async def collect_statistics(self, chunk_reader: ChunkReader) -> str:
        try:
            queue = asyncio.Queue()

            key = uuid.uuid4().hex
            saver = asyncio.create_task(self.__saver(queue, key))
            async with asyncio.TaskGroup() as tg:
                async for chunk in chunk_reader:
                    tg.create_task(self.__lemmas_count_task(chunk, queue))

            await queue.join()
            await queue.put(None)
            await saver

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

    async def __cleanup(self, key: str):
        try:
            await self.stat_storage.cleanup(key)
        finally:
            pass

    async def __saver(self, queue: asyncio.Queue, key):
        while True:
            stat: LemmasStatistics = await queue.get()

            if stat is None:
                queue.task_done()
                break

            await self.stat_storage.save(key, stat)
            queue.task_done()
