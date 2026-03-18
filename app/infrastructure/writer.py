from io import BytesIO
from typing import Generator

from xlsxwriter import Workbook


class XLSXStreamWriter:
    def __init__(self, chunk_size_kb: int = 8):
        self.chunk_size_kb = chunk_size_kb

    def writer(self, headers: list[str], data: list) -> Generator[bytes]:
        output = BytesIO()
        with Workbook(output, {"in_memory": True}) as workbook:
            ws = workbook.add_worksheet()
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            for row_idx, row in enumerate(data, start=1):
                for col_idx, value in enumerate(row):
                    ws.write(row_idx, col_idx, value)

                output.seek(0, 2)
                if output.tell() / 1024 >= self.chunk_size_kb:
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

        output.seek(0, 2)
        if output.tell() / 1024 > 0:
            yield output.getvalue()
