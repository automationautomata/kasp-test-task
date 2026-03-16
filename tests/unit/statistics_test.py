import copy
from unittest.mock import AsyncMock

import pytest

from app.services.statistics import Chunk, WordFormStatisticsError, WordFormStatistics


@pytest.fixture
def mock_lemma_counter(mocker):
    counter = mocker.Mock()
    counter.count_lemmas.return_value = {"test": 1}
    return counter


@pytest.fixture
def mock_stat_storage(mocker):
    storage = mocker.Mock()
    storage.save = AsyncMock()
    return storage


@pytest.fixture
def mock_executor(mocker):
    return mocker.Mock()


@pytest.fixture
def word_form_stat(mock_lemma_counter, mock_stat_storage, mock_executor):
    return WordFormStatistics(mock_lemma_counter, mock_stat_storage, mock_executor)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunks, expected_counts",
    [
        (
            [Chunk(0, "hello world", False), Chunk(1, "test data", True)],
            [{"test": 1}, {"test": 1}],
        ),
        (
            [Chunk(0, "one", False), Chunk(1, "two", True)],
            [{"test": 1}, {"test": 1}],
        ),
    ],
)
async def test_process_success(
    word_form_stat, mock_stat_storage, mocker, chunks, expected_counts
):
    async def chunk_reader():
        for chunk in chunks:
            yield chunk

    async def fake_run_in_executor(executor, func, data):
        return func(data)

    loop = mocker.Mock()
    loop.run_in_executor = fake_run_in_executor
    mocker.patch("asyncio.get_running_loop", return_value=loop)

    key = await word_form_stat.collect_statistics(chunk_reader())

    assert isinstance(key, str)
    assert len(key) == 32

    assert mock_stat_storage.save.call_count == len(chunks)
    calls = mock_stat_storage.save.call_args_list

    for i, call in enumerate(calls):
        args, _ = call
        assert args[0] == key
        stat = args[1]
        assert stat.ind == chunks[i].ind
        assert stat.lemmas_counts == expected_counts[i]
        assert stat.is_line_ends == chunks[i].is_line_ends


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "side_effect",
    [
        Exception("Executor error"),
        RuntimeError("boom"),
    ],
)
async def test_process_executor_exception(word_form_stat, mocker, side_effect):
    async def chunk_reader():
        yield Chunk(0, "data", False)

    loop = mocker.Mock()
    loop.run_in_executor = AsyncMock(side_effect=side_effect)
    mocker.patch("asyncio.get_running_loop", return_value=loop)

    with pytest.raises(WordFormStatisticsError):
        await word_form_stat.collect_statistics(chunk_reader())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,tokens,expected_counts,is_line_ends",
    [
        (
            "hello world hello",
            [Chunk(0, "hello world hello", True)],
            {"hello": 2, "world": 1},
            True,
        ),
        ("foo bar", [Chunk(0, "foo bar", True)], {"hello": 2, "world": 1}, True),
    ],
)
async def test_process_single_chunk(
    word_form_stat,
    mock_stat_storage,
    mocker,
    text,
    tokens,
    expected_counts,
    is_line_ends,
):
    word_form_stat.lemma_counter.count_lemmas.return_value = expected_counts

    async def chunk_reader():
        for t in tokens:
            yield t

    async def fake_run_in_executor(executor, func, data):
        return func(data)

    loop = mocker.Mock()
    loop.run_in_executor = fake_run_in_executor
    mocker.patch("asyncio.get_running_loop", return_value=loop)

    key = await word_form_stat.collect_statistics(chunk_reader())

    assert isinstance(key, str)
    assert mock_stat_storage.save.call_count == 1

    call_args = mock_stat_storage.save.call_args
    saved_key, stat = call_args[0]
    assert saved_key == key
    assert stat.ind == 0
    assert stat.lemmas_counts == expected_counts
    assert stat.is_line_ends is is_line_ends


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunks, expected_counts",
    [
        (
            [
                Chunk(0, "pytest framework", False),
                Chunk(1, "is the best", False),
                Chunk(2, "framework", True),
            ],
            [
                {"pytest": 1, "framework": 1},
                {"is": 1, "the": 1, "best": 1},
                {"framework": 1},
            ],
        ),
        (
            [Chunk(0, "", False)],
            [{}],
        ),
    ],
)
async def test_process_multiple_chunks_varied_data(
    word_form_stat, mock_stat_storage, mocker, chunks, expected_counts
):
    word_form_stat.lemma_counter.count_lemmas.side_effect = copy.deepcopy(
        expected_counts
    )

    async def chunk_reader():
        for chunk in chunks:
            yield chunk

    async def fake_run_in_executor(executor, func, data):
        return func(data)

    loop = mocker.Mock()
    loop.run_in_executor = fake_run_in_executor
    mocker.patch("asyncio.get_running_loop", return_value=loop)

    key = await word_form_stat.collect_statistics(chunk_reader())

    assert isinstance(key, str)
    assert mock_stat_storage.save.call_count == len(chunks)

    calls = mock_stat_storage.save.call_args_list

    for i, call in enumerate(calls):
        saved_key, stat = call[0]
        assert saved_key == key
        assert stat.ind == i
        assert stat.lemmas_counts == expected_counts[i]
        assert stat.is_line_ends == chunks[i].is_line_ends
