from dishka import Provider, Scope, provide

from .exporter import StatisticsExporter
from .statistics import WordFormStatistics


class ServicesProvider(Provider):
    statistics_exporter = provide(StatisticsExporter, scope=Scope.REQUEST)
    word_form_stat = provide(WordFormStatistics, scope=Scope.REQUEST)
