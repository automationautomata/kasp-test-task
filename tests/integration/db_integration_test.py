import pytest
from unittest.mock import AsyncMock

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure.storage import DBStatisticsStorage
from app.setup import init_db
from app.services.ports import LemmasStatistics, StatisticsStorageError


@pytest.fixture(scope="session")
def engine():
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    asyncio.run(init_db(engine))
    return engine


@pytest.fixture(scope="session")
def sessionmaker(engine):
    return async_sessionmaker(bind=engine)


@pytest.fixture
def db_storage(sessionmaker):
    return DBStatisticsStorage(sessionmaker)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stat",
    [
        LemmasStatistics(ind=0, lemmas_counts={}, is_line_ends=False),
        LemmasStatistics(
            ind=100, lemmas_counts={"hello": 10, "world": 5}, is_line_ends=True
        ),
    ],
)
async def test_save_and_get_single_parametrized(db_storage, stat):
    await db_storage.save("test_key", [stat])
    result = await db_storage.get("test_key")
    assert len(result) == 1
    assert result[0] == stat

    result2 = await db_storage.get("test_key")
    assert result2 == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stats",
    [
        [
            LemmasStatistics(ind=1, lemmas_counts={"a": 1}, is_line_ends=False),
            LemmasStatistics(ind=2, lemmas_counts={"b": 2}, is_line_ends=True),
            LemmasStatistics(ind=3, lemmas_counts={"c": 3, "d": 4}, is_line_ends=False),
        ],
    ],
)
async def test_save_multiple_and_get(db_storage, stats):
    await db_storage.save("test_key", stats)    

    result = await db_storage.get("test_key")
    assert len(result) == 3
    assert result == stats


@pytest.mark.asyncio
async def test_get_nonexistent_key(db_storage):
    result = await db_storage.get("not-exists")
    assert len(result) == 0


@pytest.mark.asyncio
async def test_save_error(mocker, db_storage):
    mocker.patch.object(db_storage, "save", side_effect=StatisticsStorageError())

    stat = LemmasStatistics(ind=1, lemmas_counts={}, is_line_ends=False)
    with pytest.raises(StatisticsStorageError):
        await db_storage.save("key", [stat])


@pytest.mark.asyncio
async def test_get_error(mocker, db_storage):
    mocker.patch.object(db_storage, "get", side_effect=StatisticsStorageError())

    with pytest.raises(StatisticsStorageError):
        await db_storage.get("key")
