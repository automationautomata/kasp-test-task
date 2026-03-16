import pytest

from app.services.exporter import (
    StatisticsExporter,
    StatisticsExporterError,
    ExportFormats,
)
from app.services.ports import LemmasStatistics, StatisticsStorageError


@pytest.fixture
def mock_storage(mocker):
    storage = mocker.Mock()
    storage.get = mocker.AsyncMock()
    return storage


@pytest.fixture
def mock_writers(mocker):
    writer = mocker.Mock()
    writer.writer.return_value = (chunk for chunk in [b"chunk"])

    writers = {fmt: writer for fmt in ExportFormats}
    return writers


@pytest.mark.parametrize(
    "stats, expected_rows",
    [
        (
            [
                LemmasStatistics(ind=0, lemmas_counts={"a": 1}, is_line_ends=False),
                LemmasStatistics(
                    ind=1, lemmas_counts={"a": 2, "b": 1}, is_line_ends=True
                ),
                LemmasStatistics(ind=2, lemmas_counts={"b": 3}, is_line_ends=False),
            ],
            {
                ("a", 3, "3,0"),
                ("b", 4, "1,3"),
            },
        ),
        (
            [
                LemmasStatistics(ind=0, lemmas_counts={"x": 5}, is_line_ends=True),
                LemmasStatistics(ind=1, lemmas_counts={"y": 1}, is_line_ends=False),
            ],
            {
                ("x", 5, "5,0"),
                ("y", 1, "0,1"),
            },
        ),
        (
            [LemmasStatistics(ind=0, lemmas_counts={"z": 1}, is_line_ends=False)],
            {("z", 1, "1")},
        ),
    ],
)
@pytest.mark.asyncio
async def test_statistics_exporter_builds_expected_rows(
    mock_storage, mock_writers, stats, expected_rows
):
    mock_storage.get.return_value = stats

    exporter = StatisticsExporter(mock_writers, mock_storage)

    result = list(await exporter.export("anything", ExportFormats.XLSX))

    assert result == [b"chunk"]

    mock_writers[ExportFormats.XLSX].writer.assert_called_once()
    headers, rows = mock_writers[ExportFormats.XLSX].writer.call_args[0]
    assert headers == ["словоформа", "кол-во", "кол-во по строкам"]

    assert set(rows) == expected_rows


@pytest.mark.asyncio
async def test_statistics_exporter_wraps_storage_error(mock_storage, mock_writers):
    mock_storage.get.side_effect = StatisticsStorageError()
    exporter = StatisticsExporter(mock_writers, mock_storage)

    with pytest.raises(StatisticsExporterError):
        list(await exporter.export("key", ExportFormats.XLSX))
