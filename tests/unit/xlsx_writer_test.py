import pytest
import sys
from unittest.mock import Mock

from app.infrastructure.writer import XLSXStreamWriter


@pytest.fixture(autouse=True)
def mock_xlsxwriter(mocker):
    mock_workbook = mocker.MagicMock()
    if "xlsxwriter" not in sys.modules:
        sys.modules["xlsxwriter"] = mocker.MagicMock()
    sys.modules["xlsxwriter"].Workbook = mock_workbook
    mocker.patch("app.infrastructure.writer.Workbook", mock_workbook)
    return mock_workbook


@pytest.fixture
def writer():
    return XLSXStreamWriter(chunk_size_kb=100)


@pytest.mark.parametrize(
    "headers,data,expected_writes",
    [
        (
            ["col1", "col2"],
            [("val1", "val2"), ("val3", "val4")],
            [
                (0, 0, "col1"),
                (0, 1, "col2"),
                (1, 0, "val1"),
                (1, 1, "val2"),
                (2, 0, "val3"),
                (2, 1, "val4"),
            ],
        ),
        (["single"], [("data",)], [(0, 0, "single"), (1, 0, "data")]),
        ([], [], []),
    ],
)
def test_writer_writes_headers_and_data(mocker, mock_xlsxwriter, headers, data, expected_writes):
    mock_output = Mock()
    mocker.patch("app.infrastructure.writer.BytesIO", return_value=mock_output)
    mock_output.getvalue.return_value = b"data"
    mock_output.tell.return_value = 10 

    mock_worksheet = mocker.MagicMock()
    mock_xlsxwriter.return_value.add_worksheet.return_value = mock_worksheet

    writer = XLSXStreamWriter()
    result = list(writer.writer(headers, data))

    mock_xlsxwriter.assert_called_once_with(mock_output, {"in_memory": True})

    assert result == [b"data"]


@pytest.mark.parametrize(
    "chunk_size,data,expected_chunks,getvalue_side_effect,len_side_effect",
    [
        (
            100,
            [("val1",), ("val2",), ("val3",)],
            [b"chunk1", b"chunk2"],
            [b"chunk1", b"chunk2"],
            [50, 102400, 50, 50],
        ),
        (50, [("val1",), ("val2",)], [b"chunk1"], [b"chunk1"], [30, 30, 30]),
        (
            200,
            [("val1",), ("val2",), ("val3",), ("val4",)],
            [b"chunk1"],
            [b"chunk1"],
            [100, 100, 100, 100, 100],
        ),
    ],
)
def test_writer_chunks_large_data(
    mocker, mock_xlsxwriter, chunk_size, data, expected_chunks, getvalue_side_effect, len_side_effect
):
    headers = ["col"]

    mock_output = Mock()
    mocker.patch("app.infrastructure.writer.BytesIO", return_value=mock_output)
    mock_output.getvalue.side_effect = getvalue_side_effect
    mock_output.tell.side_effect = len_side_effect
    mock_output.seek = Mock()
    mock_output.truncate = Mock()

    writer = XLSXStreamWriter(chunk_size_kb=chunk_size)
    result = list(writer.writer(headers, data))

    assert result == expected_chunks

    assert mock_output.getvalue.call_count == len(expected_chunks)
