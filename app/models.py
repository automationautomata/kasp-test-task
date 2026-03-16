import codecs
import string
from dataclasses import dataclass
from typing import AsyncGenerator, Protocol


@dataclass(frozen=True)
class Chunk:
    ind: int
    data: str
    is_line_ends: bool


class AsyncReader(Protocol):
    async def read(n: int) -> bytes: ...


class ChunkReader:
    _NONLETTERS = frozenset(string.punctuation + string.whitespace + string.digits)
    _MB = 1024 * 1024

    def __init__(self, file: AsyncReader, chunk_size: int):
        self.chunk_size = chunk_size
        self.file = file

    def __aiter__(self) -> AsyncGenerator[Chunk]:
        return self.__read()

    async def __read(self) -> AsyncGenerator[Chunk]:
        str_buf = ""
        bytes_num = self.chunk_size * self._MB

        decoder = codecs.getincrementaldecoder("utf-8")()

        i = 0
        while True:
            chunk = await self.file.read(bytes_num)
            is_final_chunk = not chunk

            str_chunk = decoder.decode(chunk, final=is_final_chunk)
            if str_buf and not str_chunk:
                i+=1
                yield Chunk(i, str_buf, False)
                return
            elif not str_chunk:
                return

            lines = str_chunk.split("\n")
            lines[0] = f"{str_buf}{lines[0]}"

            for line in lines[:-1]:
                i+=1
                yield Chunk(i, line, True)

            valid_chunk, str_buf = self.__split_by_last_nonletter(lines[-1])
            if valid_chunk:
                i+=1
                yield Chunk(i, valid_chunk, False)

            
    @classmethod
    def __split_by_last_nonletter(cls, str_chunk: str) -> tuple[str, str]:
        for i in range(len(str_chunk) - 1, 0, -1):
            if str_chunk[i] in cls._NONLETTERS:
                return str_chunk[: i + 1], str_chunk[i + 1 :]

        return "", str_chunk
