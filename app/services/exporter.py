from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Generator

from .ports import (
    StatisticsStorageError,
    StatisticsStorageProtocol,
    StreamWriter,
)


class StatisticsExporterError(Exception): ...


class ExportFormats(Enum):
    XLSX = "xlsx"


class StatisticsExporter:
    def __init__(
        self,
        writers_map: dict[ExportFormats, StreamWriter],
        stat_storage: StatisticsStorageProtocol,
    ):
        not_provided = set(ExportFormats) - set(writers_map)
        if not_provided:
            raise ValueError(
                f"StreamWriter not provided for: {', '.join(fmt.value for fmt in not_provided)} export formats"
            )

        self.stat_storage = stat_storage
        self.writers_map = writers_map

    async def export(self, key: str, format: ExportFormats) -> Generator[bytes]:
        try:
            line_stats = await self.stat_storage.get(key)
        except StatisticsStorageError as e:
            raise StatisticsExporterError from e

        lines_counter = 1
        lemma_count = defaultdict(lambda: defaultdict(int))
        for stat in line_stats:
            for lemma, count in stat.lemmas_counts.items():
                lemma_count[lemma][lines_counter] += count

            if stat.is_line_ends:
                lines_counter += 1

        rows = [None] * len(lemma_count)
        for i, (lemma, counts_per_line) in enumerate(lemma_count.items()):
            str_counts = ",".join(
                (str(counts_per_line[i]) for i in range(1, lines_counter + 1))
            )
            rows[i] = (lemma, sum(counts_per_line.values()), str_counts)

        headers = ["словоформа", "кол-во", "кол-во по строкам"]
        return self.writers_map[format].writer(headers, rows)
