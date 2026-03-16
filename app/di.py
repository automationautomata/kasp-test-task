import asyncio
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from logging import Logger, getLogger

from dishka import Provider, Scope, from_context, provide

from app.config import WorkersType

ExecutorMaxWorkers = int


MaxUploadingUsers = int


class LoggerProvider(Provider):
    @provide(scope=Scope.APP)
    def logger(self) -> Logger:
        return getLogger(__name__)


class SemaphoreProvider(Provider):
    max_uploading_users = from_context(MaxUploadingUsers, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def semaphore(self, max_uploading_users: MaxUploadingUsers) -> asyncio.Semaphore:
        return asyncio.Semaphore(max_uploading_users)


class ExecutorProvider(Provider):
    max_workers = from_context(ExecutorMaxWorkers, scope=Scope.APP)
    workers_type = from_context(WorkersType, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def executor(
        self, max_workers: ExecutorMaxWorkers, workers_type: WorkersType
    ) -> Executor:
        if workers_type == "threads":
            return ThreadPoolExecutor(max_workers=max_workers)
        return ProcessPoolExecutor(max_workers=max_workers)
