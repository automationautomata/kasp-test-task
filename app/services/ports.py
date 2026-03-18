from dataclasses import dataclass
from typing import Generator, Protocol


class LemmasCounterProtocol(Protocol):
    def count_lemmas(self, text: str) -> dict[str, int]: ...


@dataclass
class LemmasStatistics:
    ind: int
    lemmas_counts: dict[str, int]
    is_line_ends: bool


class StatisticsStorageError(Exception): ...


class StatisticsStorageProtocol(Protocol):
    async def save(self, key: str, stat: list[LemmasStatistics]): ...

    async def get(self, key: str) -> list[LemmasStatistics]: ...

    async def cleanup(self, key: str): ...


class StreamWriter(Protocol):
    def writer(self, headers: list[str], data: list) -> Generator[bytes]: ...
