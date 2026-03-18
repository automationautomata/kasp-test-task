import logging
from concurrent.futures import Executor

from dishka import Provider, Scope, provide

from .exporter import StatisticsExporter
from .ports import LemmasCounterProtocol, StatisticsStorageProtocol
from .statistics import WordFormStatistics

BatchSize = int

StatisticsLogger = logging.Logger


class StatisticsLoggerProvider(Provider):
    @provide(scope=Scope.APP)
    def logger(self, base_logger: logging.Logger) -> StatisticsLogger:
        return base_logger.getChild("statistics")


class ServicesProvider(Provider):
    statistics_exporter = provide(StatisticsExporter, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    def word_form_stat(
        self,
        lemma_counter: LemmasCounterProtocol,
        stat_storage: StatisticsStorageProtocol,
        executor: Executor,
        batch_size: BatchSize,
        logger: StatisticsLogger,
    ) -> WordFormStatistics:
        return WordFormStatistics(
            lemma_counter=lemma_counter,
            stat_storage=stat_storage,
            executor=executor,
            batch_size=batch_size,
            logger=logger,
        )
